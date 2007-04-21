#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, re, shutil, sys, tempfile, unittest

import testPlatform

sys.path.insert(0, '/usr/share/esdk/lib')
import SDK

class Callback:
    def iteration(process):
        return

class TestSDK(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        createEsdkSampleDir(self.workdir)
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

def createEsdkSampleDir(root_dir):
    # Create our directories
    for dirname in ['projects', 'platforms']:
        full_path = os.path.join(root_dir, dirname)
        os.mkdir(full_path)
    testPlatform.createSamplePlatformDir(os.path.join(root_dir, 'platforms', 'unittest'))
    
if __name__ == '__main__':
    unittest.main()
