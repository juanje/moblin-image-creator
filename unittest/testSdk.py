#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

#    Copyright (c) 2007 Intel Corporation
#
#    This program is free software; you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation; version 2 of the License
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#    or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#    for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc., 59
#    Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os, re, shutil, sys, tempfile, unittest

import testPlatform

sys.path.insert(0, '/usr/share/pdk/lib')
import SDK

class Callback:
    def iteration(process):
        return

class TestSDK(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        createPdkSampleDir(self.workdir)
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def testInstantiate(self):
        sdk = SDK.SDK(Callback())
        for key in sdk.projects:
                project = sdk.projects[key]
                a,b = (project.name, project.path)
    def testStrRepr(self):
        sdk = SDK.SDK(Callback())
        temp = sdk.__str__()
        temp = sdk.__repr__()

def createPdkSampleDir(root_dir):
    # Create our directories
    for dirname in ['projects', 'platforms']:
        full_path = os.path.join(root_dir, dirname)
        os.mkdir(full_path)
    testPlatform.createSamplePlatformDir(os.path.join(root_dir, 'platforms'), 'unittest')
    
if __name__ == '__main__':
    unittest.main()
