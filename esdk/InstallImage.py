#!/usr/bin/python -tt

import os, sys, re, tempfile, shutil

import SDK
import Project
import Mkinitrd

class InstallImage(object):
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
        self.path = os.path.join(self.target.image_path, self.name)
        self.mount_point = ''

    def __str__(self):
        return ("<InstallImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))



class LiveIsoImage(InstallImage):
    def create_image(self):
        print "LiveIsoImage: Create ISO Image here!"
        
    def __str__(self):
        return ("<LiveIsoImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class InstallIsoImage(InstallImage):
    def create_image(self):
        print "InstallIsoImage: Create Install ISO Image here!"
        
    def __str__(self):
        return ("<InstallIsoImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class BaseUsbImage(InstallImage):
    def create_container_file(self, size):
        cmd_line = "dd if=/dev/zero of=%s bs=1M count=%s" % (self.path, size)
        os.system(cmd_line)

        cmd_line = "/sbin/mkfs.vfat %s" % self.path
        os.system(cmd_line)

        # NOTE: Running syslinux on the host development system
        #       means the host and target have compatible arch.
        #       This runs syslinux inside the jailroot.
        jail_path = self.path[len(self.project.path):]
        self.project.chroot('/usr/bin/syslinux', jail_path)

    def mount_container(self):
        if not self.mount_point:
            self.mount_point = tempfile.mkdtemp('','esdk-', '/tmp')
            cmd_line = "mount -o loop -t vfat %s %s" % (self.path, self.mount_point)
            os.system(cmd_line)

    def unmount_container(self):
        if self.mount_point:
            cmd_line = "umount %s" % self.mount_point
            os.system(cmd_line)
            os.rmdir(self.mount_point)
            self.mount_point = ''

    def create_syslinux_cfg(self):
        if self.mount.point:
            cfg_file = open(os.path.join(self.mount_point, 'syslinux.cfg'), 'w')
            print >> cfg_file, """\
default linux
prompt 1
timeout 600
label linux
  kernel vmlinuz-2.6.20-default
  append initrd=initrd.img
"""
            cfg_file.close()
        
class LiveUsbImage(BaseUsbImage):
    def create_image(self):
        print "LiveUsbImage: Creating LiveUSB Image Now!"

        self.create_container_file(16)

        self.mount_container()

        initrd_path = os.path.join(self.mount_point, 'initrd.img')
        Mkinitrd.Mkinitrd().create(self.project, initrd_path)
        
        self.unmount_container()

        print "LiveUsbImage: Finished!"
        
    def __str__(self):
        return ("<LiveUsbImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class InstallUsbImage(BaseUsbImage):
    def create_image(self):
        print "InstallUsbImage: Create Install-USB Image here!"
        
    def __str__(self):
        return ("<InstallUsbImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

class HddImage(InstallImage):
    def create_image(self):
        print "HddImage: Create Hard Disk Image here!"
        
    def __str__(self):
        return ("<HddImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))



if __name__ == '__main__':
    cnt = len(sys.argv)
    if (cnt != 4) and (cnt != 2):
        print >> sys.stderr, "USAGE: %s proj_path proj_name platform_name" % (sys.argv[0])
        print >> sys.stderr, "       %s proj_name" % (sys.argv[0])
        sys.exit(1)

    sdk = SDK.SDK()

    if cnt == 4:
        proj_path = sys.argv[1]
        proj_name = sys.argv[2]
        platform_name = sys.argv[3]

        proj = sdk.create_project(proj_path, proj_name, 'test project', sdk.platforms[platform_name])
        proj.install()

        target = proj.create_target('mytest')
        target.install(sdk.platforms[platform_name].fset['Core'])

    else:
        proj_name = sys.argv[1]
        proj = sdk.projects[proj_name]

    proj.mount()

    imgLiveIso = LiveIsoImage(proj, proj.targets['mytest'], "mytest_v1-Live-DVD.iso")
    print "\nImage File Name: %s" % imgLiveIso.name
    imgLiveIso.create_image()

    imgInstallIso = InstallIsoImage(proj, proj.targets['mytest'], "mytest_v2-Install-DVD.iso")
    print "\nImage File Name: %s" % imgInstallIso.name
    imgInstallIso.create_image()

    imgLiveUsb = LiveUsbImage(proj, proj.targets['mytest'], "mytest_v3-Live-USB.bin")
    print "\nImage File Name: %s" % imgLiveUsb.name
    imgLiveUsb.create_image()

    imgInstallUsb = InstallUsbImage(proj, proj.targets['mytest'], "mytest_v4-Install-USB.bin")
    print "\nImage File Name: %s" % imgInstallUsb.name
    imgInstallUsb.create_image()

    imgHdd = HddImage(proj, proj.targets['mytest'], "mytest_v5-HDD.tar.bz2")
    print "\nImage File Name: %s" % imgHdd.name
    imgHdd.create_image()

    print "\n\nFinish!\n"
    
