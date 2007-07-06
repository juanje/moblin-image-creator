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
sys.path.insert(0, '/usr/share/pdk/lib')
import SDK
import Platform
import Project

class Callback:
    def iteration(process):
        return

# Test our base FileSystem class
class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.filesystem_dir = os.path.join(self.workdir, "filesystem")
        self.project_dir = os.path.join(self.workdir, "project")
        self.platform_name = 'unittest-platform'
        self.platform_dir = os.path.join(self.workdir, "platforms", self.platform_name)
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def testInstantiate(self):
        # Directory should not yet exist
        self.assert_(not os.path.isdir(self.filesystem_dir), "Wierd, directory exists")
        filesystem = Project.FileSystem(self.filesystem_dir, Callback())
    def testStrRepr(self):
        filesystem = Project.FileSystem(self.filesystem_dir, Callback())
        temp = filesystem.__str__()
        temp = filesystem.__repr__()
    def testEmptyValues(self):
        self.assertRaises(ValueError, Project.FileSystem, '', '')
        self.assertRaises(ValueError, Project.Project, '', '', '', '', '')
        self.assertRaises(ValueError, Project.Target, '', '', '')
    def testProjectCreation(self):
        sdk = SDK.SDK(cb = Callback(), path = self.workdir)
        platform = sdk.platforms[self.platform_name]

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-v":
        suite = unittest.TestLoader().loadTestsFromTestCase(TestFileSystem)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        unittest.main()
