#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, re, shutil, sys, tempfile, unittest
sys.path.insert(0, '/usr/share/esdk/lib')
import FSet

class TestFset(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.fset_filename = os.path.join(self.workdir, 'unittest.fset')
        self.createSampleFsetFile(self.fset_filename)
        # Create another file with same info.
        self.fset_dupfilename = os.path.join(self.workdir, 'unittest2.fset')
        self.createSampleFsetFile(self.fset_dupfilename)
    def createSampleFsetFile(self, filename):
        fset_file = open(filename, 'w')
        # Let's create a valid FSet file
        print >> fset_file, """\
[Core]
DESC=Fundamental fset that provides a root filesystem
PKGS=kernel-umd-default grub coreutils rpm
DEBUG_PKGS=kernel-umd-developer gdb yum
DEPS=

[Internet]
DESC=Internet fset pulling in basic web 2.0 capabilities
PKGS=firefox
DEBUG_PKGS=firefox-devel
DEPS=core gnome-mobile"""
        fset_file.close()
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def testInstantiate(self):
        fset = FSet.FSet()
        fset.addFile(self.fset_filename)
        if "blah" in fset:
            a = 1
        for key in fset:
            print key
    def testStrRepr(self):
        fset = FSet.FSet()
        temp = fset.__str__()
        temp = fset.__repr__()
        fset.addFile(self.fset_filename)
        temp = fset['core'].__str__()
        temp = fset['core'].__repr__()
    def testCollision(self):
        fset = FSet.FSet()
        fset.addFile(self.fset_filename)
        self.failUnlessRaises(ValueError, fset.addFile, self.fset_dupfilename)

if __name__ == '__main__':
    unittest.main()
