# Copyright 2007-2013 Lars Wirzenius
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# =*= License: GPL-3+ =*=


from distutils.core import setup

import CoverageTestRunner

setup(name='coverage-test-runner',
      version=CoverageTestRunner.__version__,
      author='Lars Wirzenius',
      author_email='liw@liw.fi',
      url='http://liw.fi/coverage-test-runner/',
      description='fail Python program unit tests unless they test everything',
      long_description='''\
 This package contains the Python module CoverageTestRunner, which runs
 unit tests implemented using the unittest module in the Python standard
 library. It each code module pairwise with its test module, with
 coverage.py, and fails unless the test module tests everything in the
 code module.
 ''',
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
      ],
      py_modules=['CoverageTestRunner'],
     )

