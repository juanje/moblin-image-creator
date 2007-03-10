#!/usr/bin/python -tt

import os, sys

from SDK import *
from Project import *

class InstallImage:
    """
    This is the base class for any type of target image output.

    This is used as the super-class for sub-classes that will generate
    installation images for a specific target and for a specific class
    of installation device/medium. Such as installation of a target system
    on a LiveUSB Key, LiveCD/DVD's, Hard Disks, and Flash Parts.
    """
    def __init__(self, project, target, dest_path):
        self.project = project
        self.target = target
        self.dest_path = os.path.abspath(os.path.expanduser(dest_path))

    def __str__(self):
        return ("<InstallImage: project=%s, target=%s, dest_path=%s>"
                % (self.project, self.target, self.dest_path))

class LiveDVDImage(InstallImage):
    def __init__(self, project, target, dest_path, img_name):
        InstallImage.__init__(self, project, target, dest_path)
        self.img_name = img_name

    def create_image(self):
        print "LiveDVDImage: Create ISO Image here!"
        
    def __str__(self):
        return ("<LiveDVDImage: project=%s, target=%s, dest_path=%s, img_name=%s>"
                % (self.project, self.target, self.dest_path, self.img_name))

class LiveUSBImage(InstallImage):
    def create_image(self):
        print "LiveUSBImage: Create & Write LiveUSB Image here!"
        
    def __str__(self):
        return ("<LiveUSBImage: project=%s, target=%s, dest_path=%s>"
                % (self.project, self.target, self.dest_path))

class InstallUSBImage(InstallImage):
    def create_image(self):
        print "InstallUSBImage: Create & Write LiveUSB Image here!"
        
    def __str__(self):
        return ("<InstallUSBImage: project=%s, target=%s, dest_path=%s>"
                % (self.project, self.target, self.dest_path))

class HDDImage(InstallImage):
    def __init__(self, project, target, dest_path, img_name):
        InstallImage.__init__(self, project, target, dest_path)
        self.img_name = img_name

    def create_image(self):
        print "HDDImage: Create Hard Disk Image here!"
        
    def __str__(self):
        return ("<HDDImage: project=%s, target=%s, dest_path=%s, img_name=%s>"
                % (self.project, self.target, self.dest_path, self.img_name))



if __name__ == '__main__':
    if len(sys.argv) != 4:
        print >> sys.stderr, "USAGE: %s path name platform" % (sys.argv[0])
        sys.exit(1)

    proj = Project(sys.argv[1], sys.argv[2], Platform(SDK(), sys.argv[3]))
    # proj.install()
    proj.create_target('mytest')
    # proj.targets['mytest'].install(proj.platform.fsets['Core'])

    dest_path = os.path.join(proj.path, "output")

    img = HDDImage(proj, proj.targets['mytest'], dest_path, "hdd.tar.bz2")
    img.create_image()
