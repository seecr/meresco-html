#!/bin/bash
## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2012-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Html"
#
# "Meresco Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

set -o errexit
rm -rf tmp build
mydir=$(cd $(dirname $0); pwd)
source /usr/share/seecr-tools/functions.d/test

pyversions=""
for i in 3.2 3.4; do
    test -e /usr/bin/python${i} && pyversions="${pyversions} ${i}"
done

VERSION="x.y.z"

for pyversion in ${pyversions}; do
    definePythonVars ${pyversion}
    echo "###### ${pyversion}, ${PYTHON}"
    ${PYTHON} setup.py install --root tmp
done
cp -r test tmp/test
removeDoNotDistribute tmp
find tmp -name '*.py' -exec sed -r -e "
    s/\\\$Version:[^\\\$]*\\\$/\\\$Version: ${VERSION}\\\$/;
    s,^docDir.*$,docDir = '${mydir}/tmp/usr/share/doc/meresco-html',;
    s,binDir = '/usr/bin',binDir = '${mydir}/tmp/usr/bin',;
    " -i '{}' \;

cp -r test tmp/test
runtests "$@"
rm -rf tmp build

