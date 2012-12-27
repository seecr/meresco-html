#!/usr/bin/env python2.5

from os import system                               #DO_NOT_DISTRIBUTE
from glob import glob                               #DO_NOT_DISTRIBUTE
from sys import path as systemPath                  #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')       #DO_NOT_DISTRIBUTE
for path in glob('../deps.d/*'):                    #DO_NOT_DISTRIBUTE
    systemPath.insert(0, path)                      #DO_NOT_DISTRIBUTE
systemPath.insert(0, '..')                          #DO_NOT_DISTRIBUTE

from sys import argv

from seecr.test import TestRunner
from _integration import IntegrationState

flags = ['--fast']

if __name__ == '__main__':
    fastMode = False
    if '--fast' in argv:
        fastMode = True
        argv.remove("--fast")

    runner = TestRunner()
    IntegrationState('default', 
        tests = [
            '_integration.servertest.ServerTest',
        ],
        fastMode=fastMode).addToTestRunner(runner)

    testnames = argv[1:]
    runner.run(testnames)
    
