#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, re, shutil, sys, tempfile, unittest

import testSdk

sys.path.insert(0, '/usr/share/esdk/lib')
import InstallImage, SDK

class TestInstallImage(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.esdk_dir = os.path.join(self.workdir, 'esdk')
        os.mkdir(self.esdk_dir)
        testSdk.createEsdkSampleDir(self.esdk_dir)

        self.project_dir = os.path.join(self.workdir, 'project')
        os.mkdir(self.project_dir)

        self.sdk = SDK.SDK(self.esdk_dir)

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
