import hashlib
from django.test import TestCase
from django.test.client import Client
from hq.models import ExtUser, Domain, Organization, ReporterProfile
from hq.tests.util import create_user_and_domain
from receiver.models import Submission
from reporters.models import Reporter

class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.domain_name = 'mockdomain'
        self.username = 'brian'
        self.password = 'test'
        user, domain = create_user_and_domain(username = self.username,
                                              password = self.password, 
                                              domain_name=self.domain_name)
        # we are explicitly testing non-traditionally logged-in authentication
        # self.client.login(username=self.username,password=self.password)
        org = Organization(name='mockorg', domain=domain)
        org.save()

    def testBasicAuth(self):
        password_hash = hashlib.sha1(self.username + ":" + self.password).hexdigest()
        authorization = "HQ username=\"%s\", password=\"%s\"" % (self.username, password_hash)
        response = self.client.post('/receiver/submit/%s' % self.domain_name, {'foo':'bar'}, \
                                    HTTP_AUTHORIZATION=authorization, 
                                    )
        submit = Submission.objects.latest()
        self.assertTrue(submit.authenticated_to!=None)

    def tearDown(self):
        user = ExtUser.objects.get(username='brian')
        user.delete()
        domain = Domain.objects.get(name=self.domain_name)
        domain.delete()