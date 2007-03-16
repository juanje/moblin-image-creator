#!/usr/bin/python -tt

import os, re, shutil, sys, tempfile, unittest
import Project

# Test our base FileSystem class
class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.filesystem_dir = os.path.join(self.workdir, "filesystem")
        self.repos_dir = os.path.join(self.workdir, "repos")
        os.mkdir(self.repos_dir)
        self.createSampleRepos()
    def createSampleRepos(self):
        filename = os.path.join(self.repos_dir, "test.repo")
        out_file = open(filename, 'w')
        # Let's create a repo
        print >> out_file, """\
[esdk-base]
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
        filesystem = Project.FileSystem(self.filesystem_dir, self.repos)
        self.assert_(os.path.isdir(self.filesystem_dir), "FileSystem did not create directory!")
    def testStrRepr(self):
        filesystem = Project.FileSystem(self.filesystem_dir, self.repos)
        temp = filesystem.__str__()
        temp = filesystem.__repr__()
    def testFileSystemStructure(self):
        filesystem = Project.FileSystem(self.filesystem_dir, self.repos)
        self.assert_(os.path.isdir(self.filesystem_dir), "FileSystem did not create directory!")
        for filename in [ 'proc', 'var/log', 'var/lib/rpm', 'dev', 'etc/yum.repos.d' ]:
            full_path = os.path.join(self.filesystem_dir, filename)
            self.assert_(os.path.exists(full_path), "Missing file/dir: %s" % filename)
        # Stuff in /etc
        for filename in [ 'hosts', 'passwd', 'group', 'resolv.conf', 'yum.conf', 'yum.repos.d' ]:
            etc_path = os.path.join("etc", filename)
            full_path = os.path.join(self.filesystem_dir, etc_path)
            self.assert_(os.path.exists(full_path), "Missing file/dir: %s" % etc_path)

if __name__ == '__main__':
    unittest.main()
