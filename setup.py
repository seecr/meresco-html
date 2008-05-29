## begin license ##
#
#    DynamicHtml is a parser that builds a parsetree for the given CQL and 
#    can convert this into other formats.
#    Copyright (C) 2005-2008 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of DynamicHtml
#
#    DynamicHtml is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    DynamicHtml is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with DynamicHtml; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from distutils.core import setup

setup(
    name='dynamichtml',
    packages=['dynamichtml'],
    version='%VERSION%',
    author='Seek You Too',
    author_email='info@cq2.nl',
    description='DynamicHtml tool to create dynamic html pages.',
    long_description='DynamicHtml tool to create dynamic html pages.',
    license='GNU Public License',
    platforms='all',
)
