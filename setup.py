## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from distutils.core import setup

from os import walk, listdir
from os.path import join
data_files = []
for path, dirs, files in walk('doc'):
    data_files.append((path.replace('doc', '/usr/share/doc/meresco-html'), [join(path, f) for f in files if f != 'license.conf']))

packages = []
for path, dirs, files in walk('meresco'):
    if '__init__.py' in files:
        packagename = path.replace('/', '.')
        if packagename == 'meresco':
            continue
        packages.append(packagename)

setup(
    name='meresco-html',
    packages=[
        'meresco',            #DO_NOT_DISTRIBUTE
    ] + packages,
    data_files=data_files,
    version='%VERSION%',
    author='Seecr (Seek You Too B.V.)',
    author_email='info@seecr.nl',
    description='Meresco Html is a template engine based on generators and a sequel to Slowfoot',
    long_description='Meresco Html is a template engine based on generators and a sequel to Slowfoot. It is also known as "DynamicHtml" or "Seecr Html"',
    license='GNU Public License',
    platforms='all',
)
