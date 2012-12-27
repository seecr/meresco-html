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

fullPythonVersion=python2.6
VERSION="x.y.z"

rm -rf tmp build
${fullPythonVersion} setup.py install --root tmp

if [ -f /etc/debian_version ]; then
    USR_DIR=`pwd`/tmp/usr/local
    SITE_PACKAGE_DIR=${USR_DIR}/lib/${fullPythonVersion}/dist-packages
else
    USR_DIR=`pwd`/tmp/usr
    SITE_PACKAGE_DIR=${USR_DIR}/lib/${fullPythonVersion}/site-packages
fi

export PYTHONPATH=${SITE_PACKAGE_DIR}:${PYTHONPATH}

cp -r test tmp/test

find tmp -type f -exec sed -r -e \
    "/DO_NOT_DISTRIBUTE/d;
    s/\\\$Version:[^\\\$]*\\\$/\\\$Version: ${VERSION}\\\$/" -i {} \;


set +o errexit
(
cd tmp/test
./alltests.sh
)
set -o errexit

rm -rf tmp build
