# -*- coding: utf-8 -*-


from os.path import isdir, join, abspath, dirname, basename
from os import system, listdir, makedirs
from sys import stdout

from seecr.test import SeecrTestCase
from random import randint
from time import sleep, time 

from subprocess import Popen
from signal import SIGTERM
from os import waitpid, kill, WNOHANG
from urllib import urlopen, urlencode
from re import compile, DOTALL
from StringIO import StringIO
from lxml.etree import parse, XMLSyntaxError, tostring

from meresco.components import readConfig

from traceback import print_exc
from seecr.test.integrationtestcase import IntegrationState as _IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator

mypath = dirname(abspath(__file__))
docDir = '/usr/share/doc/seecr-html-server'
docDir = join(dirname(dirname(mypath)), 'doc') #DO_NOT_DISTRIBUTE

class IntegrationState(_IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        _IntegrationState.__init__(self, "seecr-html-server-"+stateName, tests=tests, fastMode=fastMode)
        
        self.port = PortNumberGenerator.next()

    def binDir(self):
        binDir = '/usr/bin'
        binDir = join(dirname(dirname(mypath)), 'bin') #DO_NOT_DISTRIBUTE
        return binDir

    def setUp(self):
        self._startServer('server', self.binPath('seecr-html-server'), 'http://localhost:%s/' % self.port, port=self.port, dynamic=join(docDir, 'example', 'dynamic'), static=join(docDir, 'example', 'static'))

