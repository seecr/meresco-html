#!/usr/bin/env python2.5

from sys import path
from os import system, listdir
from os.path import isdir, join
system("find .. -name '*.pyc' | xargs rm -f")
if isdir('../deps.d'):
    for d in listdir('../deps.d'):
        path.insert(0, join('../deps.d', d))
path.insert(0, '..')

from unittest import main

from dynamichtmltest import DynamicHtmlTest

if __name__ == '__main__':
        main()
