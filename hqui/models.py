from django.db import models
from corehq.apps.domain.models import Domain


#class Application(models.Model):
#    domain = models.ForeignKey(Domain)
#    name = models.CharField(max_length=32)
#
#class Module(models.Model):
#    application = models.ForeignKey(Application)
#    name = models.CharField(max_length=32)
#
#class XForm(models.Model):
#    module = models.ForeignKey(Module)
#    name = models.CharField(max_length=32)
from couchdbkit.ext.django.schema import Document
from couchdbkit.schema.properties import StringProperty, ListProperty, DictProperty

class Application(Document):
    domain = StringProperty()
    name = StringProperty()
    modules = ListProperty()
    trans = DictProperty()