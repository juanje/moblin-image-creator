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

import testSdk

sys.path.insert(0, '/usr/share/pdk/lib')
import InstallImage, SDK

class Callback:
    def iteration(process):
        return

class TestInstallImage(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.pdk_dir = os.path.join(self.workdir, 'pdk')
        os.mkdir(self.pdk_dir)
        testSdk.createPdkSampleDir(self.pdk_dir)

        self.project_dir = os.path.join(self.workdir, 'project')
        os.mkdir(self.project_dir)

        self.sdk = SDK.SDK(path = self.pdk_dir, cb = Callback())

        self.proj_path = os.path.join(self.project_dir, 'project_unittest')
        self.proj_name = "unittest-281d8183ckd"
        self.platform_name = "unittest"

        self.proj = self.sdk.create_project(self.proj_path, self.proj_name, 'unittest project', self.sdk.platforms[self.platform_name])
        self.proj.install()

        self.target_name = 'unittest_target'
        target = self.proj.create_target(self.target_name)
        target.installFset(self.sdk.platforms[self.platform_name].fset['Core'])

        self.proj.mount()

    def tearDown(self):
        self.proj.umount()
        # have to delete the temporary project
        self.sdk.delete_project(self.proj_name)
        return
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)

    def testBasic(self):
        filename = "liveusb.bin"        
        imgLiveUsb = InstallImage.LiveUsbImage(self.proj, self.proj.targets[self.target_name], filename)
        imgLiveUsb.__str__()
        imgLiveUsb.__repr__()
        imgLiveUsb.create_image()
        os.path.join(self.proj_path, "targets", self.target_name, "fs")

if __name__ == '__main__':
    unittest.main()
