import sys
import re
import zipfile
import os
import tempfile
import shutil
from StringIO import StringIO

from models import BuildError
from xformmanager.models import MetaDataValidationError
from xformmanager.manager import XFormManager, form_translate
from xformmanager.xformdef import FormDef, ElementDef
from xformmanager.storageutility import StorageUtility

def extract_xforms( filename, dir ):
    '''Extracts the xforms from a jar file to a given directory.  
       Assumes that all xforms will be at the root of the jar.
       Returns a list of the extracted forms with absolute paths'''
    
    # hat tip: http://code.activestate.com/recipes/465649/
    zf = zipfile.ZipFile( filename )
    namelist = zf.namelist()
    filelist = filter( lambda x: not x.endswith( '/' ), namelist )
    # make base directory if it doesn't exist
    pushd = os.getcwd()
    if not os.path.isdir( dir ):
        os.mkdir( dir )
    extracted_forms = []
    # extract files that match the xforms definition 
    for filename in filelist:
        if filename.endswith(".xml") or filename.endswith(".xhtml"):
            try:
                out = open( os.path.join(dir,filename), 'wb' )
                buffer = StringIO( zf.read( filename ))
                buflen = 2 ** 20
                datum = buffer.read( buflen )
                while datum:
                    out.write( datum )
                    datum = buffer.read( buflen )
                out.close()
                extracted_forms.append(os.path.join(dir, filename))
            except Exception, e:
                logging.error("Problem extracting xform: %s, error is %s" % filename, e)
    return extracted_forms
    
def validate_jar(filename):
    '''Validates a jar for use with CommCare HQ.  It performs the following
       steps and checks:
        1. Ensures the jar is valid and contains at least one xform in the 
           root.
        2. Runs every found xform through the schema conversion logic and
           ensures that there are no problems.
        3. Runs every generated schema through validation that checks for
           the existence of a <meta> block, and that there are no missing/
           duplicate/extra tags in it.'''
    temp_directory = tempfile.mkdtemp()
    body = None
    try: 
        xforms = extract_xforms(filename, temp_directory)
        if not xforms:
            raise BuildError("Jar file must have at least 1 xform")
        # now run through each of the forms and try to convert to 
        # a schema
        for xform in xforms:
            body = open(xform, "r")
            output, errorstream, has_error = form_translate(xform, body.read())
            if has_error:
                raise BuildError("Could not convert xform (%s) to schema.  Your error is %s" % 
                                 (xform, errorstream))
            # if no errors, we should have a valid schema in the output
            # check the meta block, by creating a formdef object and inspecting it
            formdef = FormDef(StringIO(output))
            if not formdef:
                raise BuildError("Could not get a valid form definition from the xml file: %s"
                                  % xform)
            meta_element = formdef.get_meta_element()
            if not meta_element:
                raise BuildError("From %s had no meta block!" % xform)
            
            meta_issues = StorageUtility.get_meta_validation_errors(meta_element)
            if meta_issues:
                raise MetaDataValidationError(meta_issues, xform)
            # if we made it here we're all good
    finally:
        # clean up after ourselves
        if body:
            body.close()
        shutil.rmtree(temp_directory)