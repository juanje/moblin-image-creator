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

import os
import re
import shutil
import sys
import tempfile
import traceback

import Mkinitrd
import Project
import SDK

class SyslinuxCfg(object):
    def __init__(self, path, cfg_filename):
        try:
            self.path = path
            self.cfg_filename = cfg_filename
            self.cfg_path = os.path.join(self.path, cfg_filename)
            self.msg_path = os.path.join(self.path, 'boot.msg')
            self.index = 1

            welcome_mesg = "Welcome to the Linux PDK:"

            # Create and initialize the syslinux config file
            cfg_file = open(self.cfg_path, 'w')
            print >> cfg_file, """\
    prompt 1
    timeout 600
    display boot.msg
    """
            cfg_file.close()

            # Create and initialize the syslinux boot message file
            msg_file = open(self.msg_path, 'w')
            msg_file.write("\f")
            print >> msg_file, "\n" + welcome_mesg + "\n"
            msg_file.close()
        except:
            print_exc_plus()
            sys.exit(1)
            
    def __repr__(self):
        return 'SyslinuxCfg(path = "%s", cfg_filename = "%s")' % (self.path,
            self.cfg_filename)

    def __str__(self):
        return "<SyslinuxCfg: __dict__=%s>" % self.__dict__

    def add_default(self, kernel, append = 'initrd=initrd.img'):
        label = 'linux'
        kernel_file = 'vmlinuz'

        # Add the default entry to the syslinux config file
        cfg_file = open(self.cfg_path, 'a ')
        print >> cfg_file, "default " + label
        print >> cfg_file, "label " + label
        print >> cfg_file, "  kernel " + kernel_file
        print >> cfg_file, "  append " + append
        cfg_file.close()

        # Add the default entry in the syslinux boot message file
        msg_file = open(self.msg_path, 'a ')
        msg_file.write("- To boot default " + kernel + " kernel, press " + chr(15) + \
                       "\x01<ENTER>" +  chr(15) + "\x07\n\n")
        msg_file.close()
        return kernel_file

    def add_target(self, kernel, append = 'initrd=initrd.img'):
        label = "linux%s" % self.index
        kernel_file = "linux%s" % self.index
        self.index += 1

        # Add the target to the syslinux config file
        cfg_file = open(self.cfg_path, 'a ')
        print >> cfg_file, "label " + label
        print >> cfg_file, "  kernel " + kernel_file
        print >> cfg_file, "  append " + append
        cfg_file.close()

        # Add the target to the syslinux boot message file
        msg_file = open(self.msg_path, 'a ')
        msg_file.write("- To boot " + kernel + " kernel, type: " + chr(15) + \
                       "\x01" + label + " <ENTER>" +  chr(15) + "\x07\n\n")
        msg_file.close()
        return kernel_file

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
        self.tmp_path = ''
        self.rootfs = ''
        self.rootfs_path = ''
        self.kernels = []
        for file in os.listdir(os.path.join(self.target.fs_path, 'boot')):
            if file.find('vmlinuz') == 0:
                self.kernels.append(file)
        if not self.kernels:
            raise ValueError("no kernels were found")
        self.kernels.sort()
        self.default_kernel = self.kernels.pop(0)
        self.default_kernel_mod_path = os.path.join(self.target.fs_path, 'lib', 'modules', self.default_kernel.split('vmlinuz-').pop().strip())

    def install_kernels(self, cfg_filename):
        if not self.tmp_path:
            raise ValueError, "tmp_path doesn't exist"

        s = SyslinuxCfg(self.tmp_path, cfg_filename)

        # Copy the default kernel
        kernel_name = s.add_default(self.default_kernel, 'initrd=initrd.img root=rootfs.img')
        src_path = os.path.join(self.target.fs_path, 'boot', self.default_kernel)
        dst_path = os.path.join(self.tmp_path, kernel_name)
        shutil.copyfile(src_path, dst_path)

        # Copy the remaining kernels
        for k in self.kernels:
            kernel_name = s.add_target(k, 'initrd=initrd.img root=rootfs.img')
            src_path = os.path.join(self.target.fs_path, 'boot', k)
            dst_path = os.path.join(self.tmp_path, kernel_name)
            shutil.copyfile(src_path, dst_path)

    def create_fstab(self):
        fstab_file = open(os.path.join(self.target.fs_path, 'etc/fstab'), 'w')
        print >> fstab_file, """\
/dev/devpts             /dev/pts                devpts  gid=5,mode=620  0 0
/dev/shm                /dev/shm                tmpfs   defaults        0 0
/dev/proc               /proc                   proc    defaults        0 0
/dev/sys                /sys                    sysfs   defaults        0 0

"""
        fstab_file.close()

    def create_modules_dep(self):
        base_dir = self.target.fs_path[len(self.project.path):]
        boot_path = os.path.join(self.target.fs_path, 'boot')
        
        for file in os.listdir(boot_path):
            if file.find('System.map-') == 0:
                kernel_version = file[len('System.map-'):]

                tmp_str = "lib/modules/%s/modules.dep" % kernel_version
                moddep_file = os.path.join(self.target.fs_path, tmp_str)

                if os.path.isfile(moddep_file):
                    sr_deps = os.stat(moddep_file)
                    sr_sym  = os.stat(os.path.join(boot_path, file))
                    
                    # Skip generating a new modules.dep if the Symbols are
                    # older than the current modules.dep file.
                    if sr_deps.st_mtime > sr_sym.st_mtime: 
                        continue

                symbol_file = os.path.join(base_dir, 'boot', file)

                cmd_args = "-b %s -v %s -F %s" % (base_dir, kernel_version, symbol_file)
                self.project.chroot("/sbin/depmod", cmd_args)

    def create_rootfs(self):
        if not os.path.isfile(os.path.join(self.target.fs_path, 'etc/fstab')):
            self.create_fstab()

        self.create_modules_dep()

        self.rootfs = 'rootfs.img'
        self.rootfs_path = os.path.join(self.target.image_path, self.rootfs)
        if os.path.isfile(self.rootfs_path):
            os.remove(self.rootfs_path)
        
        fs_path      = self.target.fs_path[len(self.project.path):]
        exclude_path = os.path.join(fs_path, 'boot')
        image_path   = self.target.image_path[len(self.project.path):]
        image_path   = os.path.join(image_path,'rootfs.img')
        cmd_args     = "%s %s -e %s" % (fs_path, image_path, exclude_path)

        self.project.chroot("/usr/sbin/mksquashfs", cmd_args)
            
    def delete_rootfs(self):
        if self.rootfs and os.path.isfile(self.rootfs_path):
            os.remove(self.rootfs_path)
            self.rootfs = ''
            self.rootfs_path = ''

    def create_bootfs(self):
        self.bootfs = 'bootfs.img'
        self.bootfs_path = os.path.join(self.target.image_path, self.bootfs)
        if os.path.isfile(self.bootfs_path):
            os.remove(self.bootfs_path)
        
        fs_path      = self.target.fs_path[len(self.project.path):]
        fs_path      = os.path.join(fs_path, 'boot')
        image_path   = self.target.image_path[len(self.project.path):]
        image_path   = os.path.join(image_path,'bootfs.img')
        cmd_args     = "%s %s" % (fs_path, image_path)

        self.project.chroot("/usr/sbin/mksquashfs", cmd_args)
            

    def delete_bootfs(self):
        if self.bootfs and os.path.isfile(self.bootfs_path):
            os.remove(self.bootfs_path)
            self.bootfs = ''
            self.bootfs_path = ''

    def create_install_script(self, path):
        install_file = open(os.path.join(path, 'install.sh'), 'w')
        print >> install_file, """\
#!/bin/bash

echo -e '\nDeleting Partition Table on /dev/hda...\n'
dd if=/dev/zero of=/dev/hda bs=512 count=2
sync

echo -e 'Creating New Partiton Table on /dev/hda...\n'
fdisk /dev/hda <<EOF
n
p
1
1
+1024M
n
p
2


a
1
w
EOF

sync

echo -e 'Formatting /dev/hda1 w/ ext2...\n'
mkfs.ext2 /dev/hda1
sync

echo -e 'Formatting /dev/hda2 w/ ext3...\n'
mkfs.ext3 /dev/hda2
sync

echo -e 'Mounting partitions...\n'
mkdir /tmp/install
mount /dev/sda /tmp/install

mkdir /tmp/boot
mount -o loop -t squashfs /tmp/install/bootfs.img /tmp/boot

mount /dev/hda2 /mnt
mkdir /mnt/boot
mount /dev/hda1 /mnt/boot

echo -e 'Copying system files onto hard disk drive...\n'
cp -v /tmp/install/rootfs.img /mnt/boot
cp -av /tmp/boot /mnt

/usr/sbin/grub-install --root-directory=/mnt /dev/hda

echo -e 'Unmounting partitions...\n'
umount /mnt/boot
umount /mnt
umount /tmp/boot
umount /tmp/install

echo -e '\n\n\nInstall Finished!\n\n'
echo -e 'System shutting down!\n\n'
echo -e 'Disconnect the USB-Key when shutdown is complete and\n'
echo -e 'Reboot the system from HDD...\n\n'

sleep 10
exec init 0
"""
        install_file.close()

        
    def __str__(self):
        return ("<InstallImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))


class LiveIsoImage(InstallImage):
    def create_image(self):
        raise ValueError("LiveIsoImage: Create ISO Image not implemented!")
        
    def __str__(self):
        return ("<LiveIsoImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))


class InstallIsoImage(InstallImage):
    def create_image(self):
        raise ValueError("InstallIsoImage: Create Install ISO Image not implemented!")
        
    def __str__(self):
        return ("<InstallIsoImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))


class BaseUsbImage(InstallImage):
    def install_kernels(self):
        InstallImage.install_kernels(self, 'syslinux.cfg')
        
    def create_container_file(self, size):
        out_file = open(self.path, 'w')
        # Make a kibibyte length string of zeroes
        out_string = chr(0) * 1024
        # Write the string out to the file to create file of size * mibibyte in length
        for count in range(0, size * 1024):
            out_file.write(out_string)
        out_file.close()

        cmd_line = "/sbin/mkfs.vfat %s" % self.path
        result = os.system(cmd_line)
        if result:
            print >> sys.stderr, "Error running command: %s" % cmd_line
            raise EnvironmentError, "Error running command: %s" % cmd_line

        # NOTE: Running syslinux on the host development system
        #       means the host and target have compatible architectures.
        #       This runs syslinux inside the jailroot so the correct
        #       version of syslinux is used.
        jail_path = self.path[len(self.project.path):]
        self.project.chroot('/usr/bin/syslinux', jail_path)

    def mount_container(self):
        if not self.tmp_path:
            self.tmp_path = tempfile.mkdtemp('','pdk-', '/tmp')
            cmd_line = "mount -o loop -t vfat %s %s" % (self.path, self.tmp_path)
            result = os.system(cmd_line)
            if result:
                print >> sys.stderr, "Error running command: %s" % cmd_line
                raise EnvironmentError, "Error running command: %s" % cmd_line

    def umount_container(self):
        if self.tmp_path:
            cmd_line = "umount %s" % self.tmp_path
            result = os.system(cmd_line)
            if result:
                print >> sys.stderr, "Error running command: %s" % cmd_line
                raise EnvironmentError, "Error running command: %s" % cmd_line
            os.rmdir(self.tmp_path)
            self.tmp_path = ''

class LiveUsbImage(BaseUsbImage):
    def create_image(self, fs_type='RAMFS'):
        print "LiveUsbImage: Creating LiveUSB Image(%s) Now..." % fs_type
        Mkinitrd.create(self.project, '/tmp/.tmp.initrd', kernel_mod_path=self.default_kernel_mod_path)
        self.create_rootfs()
        initrd_stat_result = os.stat('/tmp/.tmp.initrd')
        rootfs_stat_result = os.stat(self.rootfs_path)
        size = ((rootfs_stat_result.st_size + initrd_stat_result.st_size) / (1024 * 1024)) + 64
        if fs_type == 'EXT3FS':
           size = size + 100
        self.create_container_file(size)
        self.mount_container()
        initrd_path = os.path.join(self.tmp_path, 'initrd.img')
        shutil.move('/tmp/.tmp.initrd', initrd_path)
        self.install_kernels()
        shutil.copy(self.rootfs_path, self.tmp_path)
        self.umount_container()
        self.delete_rootfs()
        print "LiveUsbImage: Finished!"
        
    def __str__(self):
        return ("<LiveUsbImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))


class InstallUsbImage(BaseUsbImage):
    def create_image(self):
        print "InstallUsbImage: Creating InstallUSB Image..."
        Mkinitrd.create(self.project, '/tmp/.tmp.initrd', kernel_mod_path=self.default_kernel_mod_path)
        self.create_rootfs()
        self.create_bootfs()
        initrd_stat_result = os.stat('/tmp/.tmp.initrd')
        rootfs_stat_result = os.stat(self.rootfs_path)
        bootfs_stat_result = os.stat(self.bootfs_path)
        size = ((rootfs_stat_result.st_size + bootfs_stat_result.st_size + initrd_stat_result) / (1024 * 1024)) + 64
        self.create_container_file(size)
        self.mount_container()
        initrd_path = os.path.join(self.tmp_path, 'initrd.img')
        shutil.move('/tmp/.tmp.initrd', initrd_path)
        self.install_kernels()
        shutil.copy(self.rootfs_path, self.tmp_path)
        shutil.copy(self.bootfs_path, self.tmp_path)
        self.create_install_script(self.tmp_path)
        self.umount_container()
        self.delete_rootfs()
        self.delete_bootfs()
        print "InstallUsbImage: Finished!"
        print "\nYou can now use the image to boot and install the target file-system on the target device's HDD.\n"
        print "\nWARNING: Entire contents of the target devices's HDD will be erased prior to installation!"
        print "         This includes ALL partitions on the disk!\n"
        
    def __str__(self):
        return ("<InstallUsbImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))


class HddImage(InstallImage):
    def create_image(self):
        raise ValueError("HddImage: Create Hard Disk Image not implemented!")
        
    def __str__(self):
        return ("<HddImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

def print_exc_plus():
    # From Python Cookbook 2nd Edition.  FIXME: Will need to remove this at
    # some point, or give attribution.
    """ Print the usual traceback information, followed by a listing of
        all the local variables in each frame.
    """
    tb = sys.exc_info()[2]
    while tb.tb_next:
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    traceback.print_exc()
    print "Locals by frame, innermost last"
    for frame in stack:
        print
        print "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            print "\t%20s = " % key,
            # we must _absolutely_ avoid propagating exceptions, and str(value)
            # COULD cause any exception, so we MUST catch any...:
            try:
                print value
            except:
                print "<ERROR WHILE PRINTING VALUE>"
    traceback.print_exc()

class Callback:
    def iteration(process):
        return

if __name__ == '__main__':
    cnt = len(sys.argv)
    if (cnt != 4) and (cnt != 2):
        print >> sys.stderr, "USAGE: %s proj_path proj_name platform_name" % (sys.argv[0])
        print >> sys.stderr, "       %s proj_name" % (sys.argv[0])
        sys.exit(1)

    sdk = SDK.SDK(Callback())

    if cnt == 4:
        proj_path = sys.argv[1]
        proj_name = sys.argv[2]
        platform_name = sys.argv[3]

        proj = sdk.create_project(proj_path, proj_name, 'test project', sdk.platforms[platform_name])
        proj.install()

        target = proj.create_target('mytest')
        target.installFset(sdk.platforms[platform_name].fset['Core'])

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
    
