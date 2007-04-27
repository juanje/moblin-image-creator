#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, re, shutil, sys, tempfile, unittest
sys.path.insert(0, '/usr/share/pdk/lib')
import SDK
import Platform
import Project

import testPlatform

class Callback:
    def iteration(process):
        return

# Test our base FileSystem class
class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.filesystem_dir = os.path.join(self.workdir, "filesystem")
        self.project_dir = os.path.join(self.workdir, "project")
        self.repos_dir = os.path.join(self.workdir, "repos")
        os.mkdir(self.repos_dir)
        self.createSampleRepos()
        self.platform_name = 'unittest-platform'
        self.platform_dir = os.path.join(self.workdir, "platforms", self.platform_name)
        testPlatform.createSamplePlatformDir(self.platform_dir)
    def createSampleRepos(self):
        filename = os.path.join(self.repos_dir, "test.repo")
        out_file = open(filename, 'w')
        # Let's create a repo
        print >> out_file, """\
[pdk-base]
name=Fedora Core $releasever - $basearch - Base
baseurl=http://linux-ftp.jf.intel.com/pub/mirrors/fedora/linux/core/6/$basearch/os/
enabled=1
gpgcheck=0"""
        out_file.close()
        self.repos = [ filename ]
    def tearDown(self):
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir)
    def testInstantiate(self):
        # Directory should not yet exist
        self.assert_(not os.path.isdir(self.filesystem_dir), "Wierd, directory exists")
        filesystem = Project.FileSystem(self.filesystem_dir, self.repos, Callback())
        self.assert_(os.path.isdir(self.filesystem_dir), "FileSystem did not create directory!")
    def testStrRepr(self):
        filesystem = Project.FileSystem(self.filesystem_dir, self.repos, Callback())
        temp = filesystem.__str__()
        temp = filesystem.__repr__()
    def testEmptyValues(self):
        self.assertRaises(ValueError, Project.FileSystem, '', '', '')
        self.assertRaises(ValueError, Project.Project, '', '', '', '', '')
        self.assertRaises(ValueError, Project.Target, '', '', '')
    def testProjectCreation(self):
        sdk = SDK.SDK(cb = Callback(), path = self.workdir)
        platform = sdk.platforms[self.platform_name]
        #print "Skipping project creation..."
        #project = sdk.create_project(self.project_dir, 'unittest-proj', 'unittest project', platform)
    def testFileSystemStructure(self):
        filesystem = Project.FileSystem(self.filesystem_dir, self.repos, Callback())
        self.assert_(os.path.isdir(self.filesystem_dir), "FileSystem did not create directory!")
        for filename in [ 'proc', 'var/log', 'var/lib/rpm', 'dev', 'etc/yum.repos.d' ]:
            full_path = os.path.join(self.filesystem_dir, filename)
            self.assert_(os.path.exists(full_path), "Missing file/dir: %s" % filename)
        # Stuff in /etc
        for filename in [ 'hosts', 'resolv.conf', 'yum.conf', 'yum.repos.d' ]:
            etc_path = os.path.join("etc", filename)
            full_path = os.path.join(self.filesystem_dir, etc_path)
            self.assert_(os.path.exists(full_path), "Missing file/dir: %s" % etc_path)

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-v":
        suite = unittest.TestLoader().loadTestsFromTestCase(TestFileSystem)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        unittest.main()
