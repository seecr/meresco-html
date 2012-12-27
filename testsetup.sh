#!/bin/bash
## begin license ##
# 
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot. 
# It is also known as "DynamicHtml". 
# 
# Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Seecr Html"
# 
# "Seecr Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Seecr Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Seecr Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

set -e
rm -rf tmp build
mydir=$(cd $(dirname $0); pwd)
source /usr/share/seecr-test/functions

VERSION="x.y.z"

definePythonVars

${PYTHON} setup.py install --root tmp
cp seecr/__init__.py ${SITEPACKAGES}/seecr/
cp -r test tmp/test
find tmp -type f -exec sed -r -e \
    "s,^docDir.*$,docDir = '$mydir/tmp/usr/share/doc/seecr-html'," -i {} \;

removeDoNotDistribute tmp

runtests "$@"

rm -rf tmp build
