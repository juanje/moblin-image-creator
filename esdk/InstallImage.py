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
    def __init__(self, project, target, name):
        self.project = project
        self.target = target
        self.name = name

    def __str__(self):
        return ("<InstallImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class LiveIsoImage(InstallImage):
    def __init__(self, project, target, name):
        InstallImage.__init__(self, project, target, name)
        self.name = name + '-Live-DVD.iso'

    def create_image(self):
        print "LiveIsoImage: Create ISO Image here!"
        
    def __str__(self):
        return ("<LiveIsoImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class InstallIsoImage(InstallImage):
    def __init__(self, project, target, name):
        InstallImage.__init__(self, project, target, name)
        self.name = name + '-Install-DVD.iso'

    def create_image(self):
        print "InstallIsoImage: Create Install ISO Image here!"
        
    def __str__(self):
        return ("<InstallIsoImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class LiveUsbImage(InstallImage):
    def __init__(self, project, target, name):
        InstallImage.__init__(self, project, target, name)
        self.name = name + '-Live-USB.bin'

    def create_image(self):
        print "LiveUsbImage: Create LiveUSB Image here!"
        
    def __str__(self):
        return ("<LiveUsbImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class InstallUsbImage(InstallImage):
    def __init__(self, project, target, name):
        InstallImage.__init__(self, project, target, name)
        self.name = name + '-Install-USB.bin'

    def create_image(self):
        print "InstallUsbImage: Create Install-USB Image here!"
        
    def __str__(self):
        return ("<InstallUsbImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class HddImage(InstallImage):
    def __init__(self, project, target, name):
        InstallImage.__init__(self, project, target, name)
        self.name = name + '-HDD-Image.tar.bz2'

    def create_image(self):
        print "HddImage: Create Hard Disk Image here!"
        
    def __str__(self):
        return ("<HddImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))



if __name__ == '__main__':
    if len(sys.argv) != 4:
        print >> sys.stderr, "USAGE: %s path name platform" % (sys.argv[0])
        sys.exit(1)

    proj = Project(sys.argv[1], sys.argv[2], Platform('/usr/share/esdk', sys.argv[3]))
    proj.install()
    proj.create_target('mytest')
    proj.targets['mytest'].install(proj.platform.fsets['Core'])

    dest_path = os.path.join(proj.path, "output")

    imgLiveIso = LiveIsoImage(proj, proj.targets['mytest'], "mytest_v1")
    print "\nImage File Name: %s" % imgLiveIso.name
    imgLiveIso.create_image()

    imgInstallIso = InstallIsoImage(proj, proj.targets['mytest'], "mytest_v2")
    print "\nImage File Name: %s" % imgInstallIso.name
    imgInstallIso.create_image()

    imgLiveUsb = LiveUsbImage(proj, proj.targets['mytest'], "mytest_v3")
    print "\nImage File Name: %s" % imgLiveUsb.name
    imgLiveUsb.create_image()

    imgInstallUsb = InstallUsbImage(proj, proj.targets['mytest'], "mytest_v4")
    print "\nImage File Name: %s" % imgInstallUsb.name
    imgInstallUsb.create_image()

    imgHdd = HddImage(proj, proj.targets['mytest'], "mytest_v5")
    print "\nImage File Name: %s" % imgHdd.name
    imgHdd.create_image()

    print "\n\nFinish!\n"
    
