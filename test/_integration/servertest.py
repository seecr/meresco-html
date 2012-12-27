
from seecr.test.integrationtestcase import IntegrationTestCase
from seecr.test.utils import getRequest

class ServerTest(IntegrationTestCase):
    def testServer(self):
        header, body = getRequest(path='/', port=self.port, parse=False)
