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

import Project
import SDK
import mic_cfg
import pdk_utils

debug = False
if mic_cfg.config.has_option('general', 'debug'):
    debug = int(mic_cfg.config.get('general', 'debug'))

class SyslinuxCfg(object):
    """Class to provide helper functions for doing the syslinux stuff.
    Syslinux home page: http://syslinux.zytor.com/"""
    def __init__(self, project, path, cfg_filename, message_color, message):
        try:
            self.project = project
            self.path = path
            self.cfg_filename = cfg_filename
            self.cfg_path = os.path.join(self.path, cfg_filename)
            self.msg_path = os.path.join(self.path, 'boot.msg')
            self.index = 1

            for section in [ "installimage.%s" % self.project.platform.name, "installimage" ]:
                if mic_cfg.config.has_section(section):
                   # section is now set to the appropriate section
                   break
            welcome_mesg = mic_cfg.config.get(section, "welcome_message")
            # Create and initialize the syslinux config file
            cfg_file = open(self.cfg_path, 'w')
            print >> cfg_file, """\
    prompt 1
    display boot.msg
    """
            cfg_file.close()
            # Create and initialize the syslinux boot message file
            msg_file = open(self.msg_path, 'w')
            msg_file.write("\f")
            print >> msg_file, "\n" + welcome_mesg + "\n"
            msg_file.close()
            self.setMessage(message_color, message)
        except:
            if debug: print_exc_plus()
            sys.exit(1)

    def setMessage(self, message_color, message):
        """message_color is the 2 bytes to set the background and foreground
        color as documented in the syslinux documentation under DISPLAY file
        format

        <SI><bg><fg>                            <SI> = <Ctrl-O> = ASCII 15
        Set the display colors to the specified background and
        foreground colors, where <bg> and <fg> are hex digits,
        corresponding to the standard PC display attributes:

        0 = black               8 = dark grey
        1 = dark blue           9 = bright blue
        2 = dark green          a = bright green
        3 = dark cyan           b = bright cyan
        4 = dark red            c = bright red
        5 = dark purple         d = bright purple
        6 = brown               e = yellow
        7 = light grey          f = white

        Picking a bright color (8-f) for the background results in the
        corresponding dark color (0-7), with the foreground flashing.
        """
        if len(message_color) != 2:
            raise ValueError("message_color string must be 2 bytes long.  Passed in string was: %s bytes long.  String: %s" % (len(message_color), message(color)))
        msg_file = open(self.msg_path, 'a ')
        msg_file.write(chr(15) + message_color)
        msg_file.write(message)
        # Set it back to light gray on black
        print >> msg_file, chr(15) + "07"

    def __repr__(self):
        return 'SyslinuxCfg(path = "%s", cfg_filename = "%s")' % (self.path,
            self.cfg_filename)

    def __str__(self):
        return "<SyslinuxCfg: __dict__=%s>" % self.__dict__

    def add_default(self, kernel, append = 'initrd=initrd.img'):
        label = 'linux'
        append = re.sub(r'initrd.img',"initrd0.img", append)
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
        msg_file.write("- To boot default " + kernel + " kernel, press " + \
            chr(15) + "0f<ENTER>" +  chr(15) + "07\n\n")
        msg_file.close()
        return kernel_file

    def add_target(self, kernel, append = 'initrd=initrd.img'):
        label = "linux%s" % self.index
        kernel_file = "linux%s" % self.index
        append = re.sub(r'initrd.img',"initrd%d.img" % self.index, append)
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
    def __init__(self, project, target, name, progress_callback = None):
        self.project = project
        self.target = target
        self.name = name
        self.progress_callback = progress_callback
        self.path = os.path.join(self.target.image_path, self.name)
        self.tmp_path = ''
        self.rootfs = ''
        self.rootfs_path = ''
        self.kernels = []
        self.default_kernel = ''
        # Find the config section for whole class usage 
        for section in [ "installimage.%s" % self.project.platform.name, "installimage" ]:
            if mic_cfg.config.has_section(section):
                # section is now set to the appropriate section
                break
        self.section = section
        for filename in os.listdir(os.path.join(self.target.fs_path, 'boot')):
            if filename.find('vmlinuz') == 0:
                if (not self.default_kernel) and (filename.find('default') > 0):
                    self.default_kernel = filename
                else:
                    self.kernels.append(filename)
        if (not self.kernels) and (not self.default_kernel):
                raise ValueError("no kernels were found")
        self.kernels.sort()
        if not self.default_kernel:
            self.default_kernel = self.kernels.pop(0)
        self.default_kernel_mod_path = os.path.join(self.target.fs_path, 'lib', 'modules', self.default_kernel.split('vmlinuz-').pop().strip())
        self.exclude_file = os.path.join(self.project.platform.path, 'exclude')

    def install_kernels(self, cfg_filename, message_color, message, imageType='USBImage'):
        if not self.tmp_path:
            raise ValueError, "tmp_path doesn't exist"

        s = SyslinuxCfg(self.project, self.tmp_path, cfg_filename, message_color, message)
        # Copy the default kernel
        if imageType == 'CDImage':
            kernel_name = s.add_default(self.default_kernel, self.project.get_target_cd_kernel_cmdline(self.target.name))
        else:
            kernel_name = s.add_default(self.default_kernel, self.project.get_target_usb_kernel_cmdline(self.target.name))
        src_path = os.path.join(self.target.fs_path, 'boot', self.default_kernel)
        dst_path = os.path.join(self.tmp_path, kernel_name)
        shutil.copyfile(src_path, dst_path)
        # Copy the remaining kernels
        for kernel in self.kernels:
            if imageType == 'CDImage':
                kernel_name = s.add_target(kernel, self.project.get_target_cd_kernel_cmdline(self.target.name))
            else:
                kernel_name = s.add_target(kernel, self.project.get_target_usb_kernel_cmdline(self.target.name))
            src_path = os.path.join(self.target.fs_path, 'boot', kernel)
            dst_path = os.path.join(self.tmp_path, kernel_name)
            shutil.copyfile(src_path, dst_path)

    def create_fstab(self, swap = True):
        fstab_file = open(os.path.join(self.target.fs_path, 'etc/fstab'), 'w')
        print >> fstab_file, "unionfs	    /	            unionfs defaults	0 0"
        print >> fstab_file, "proc			/proc			proc	defaults	0 0"
        if swap:
            print >> fstab_file, "/dev/sda3		none			swap	sw		0 0"
        fstab_file.close()

    def create_modules_dep(self):
        base_dir = self.target.fs_path[len(self.project.path):]
        boot_path = os.path.join(self.target.fs_path, 'boot')
        
        for filename in os.listdir(boot_path):
            if filename.find('System.map-') == 0:
                kernel_version = filename[len('System.map-'):]

                tmp_str = "lib/modules/%s/modules.dep" % kernel_version
                moddep_file = os.path.join(self.target.fs_path, tmp_str)

                symbol_file = os.path.join(base_dir, 'boot', filename)

                cmd = "depmod -b %s -v %s -F %s" % (base_dir, kernel_version, symbol_file)
                self.project.chroot(cmd)

    def create_rootfs(self):
        """Create the root file system, using mksquashfs.  If we don't want to
        use squashfs on the device then the content will be copied out of the
        squashfs image during the install"""
        print "Creating root file system..."
        # re-create fstab every time, since user could change fstab options on
        # the fly (by editing image-creator.cfg)
        fstab_path = os.path.join(self.target.fs_path, 'etc/fstab')
        if int(mic_cfg.config.get(self.section, "swap_option")) == 2:
            swap = True
        else:
            swap = False
        self.create_fstab(swap)
        self.create_modules_dep()
        self.rootfs = 'rootfs.img'
        self.rootfs_path = os.path.join(self.target.image_path, self.rootfs)
        if os.path.isfile(self.rootfs_path):
            os.remove(self.rootfs_path)
        
        fs_path      = self.target.fs_path[len(self.project.path):]
        image_path   = self.target.image_path[len(self.project.path):]
        image_path   = os.path.join(image_path,'rootfs.img')
        cmd          = "mksquashfs %s %s -no-progress -ef %s" % (fs_path, image_path, self.exclude_file)
        self.write_manifest(self.path)
        self.target.umount()
        print "Executing the mksquashfs program: %s" % cmd
        self.project.chroot(cmd)
        self.target.mount()
            
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
        print "Creating bootfs at: %s" % self.bootfs_path
        # Remove old initrd images
        for file in os.listdir(os.path.join(self.target.fs_path, 'boot')):
            if file.find('initrd.img') == 0:
                os.remove(os.path.join(self.target.fs_path, 'boot', file))
        self.kernels.insert(0,self.default_kernel)
        # copy pre-created initrd img (by create_all_initramfs) for each installed kernel
        for count, kernel in enumerate(self.kernels):
            version_str = kernel.split('vmlinuz-').pop().strip()
            initrd_name = "initrd.img-" + version_str
            shutil.copy("/tmp/.tmp.initrd%d" % count, os.path.join(self.target.fs_path, 'boot', initrd_name))
        self.kernels.pop(0)
        fs_path    = self.target.fs_path[len(self.project.path):]
        fs_path    = os.path.join(fs_path, 'boot')
        image_path = self.target.image_path[len(self.project.path):]
        image_path = os.path.join(image_path,'bootfs.img')
        cmd        = "mksquashfs %s %s -no-progress" % (fs_path, image_path)
        self.project.chroot(cmd)

    def delete_bootfs(self):
        if self.bootfs and os.path.isfile(self.bootfs_path):
            os.remove(self.bootfs_path)
            self.bootfs = ''
            self.bootfs_path = ''

    def create_install_script(self, output_dir):
        shutil.copy(os.path.join(self.project.platform.path, 'install.sh'), output_dir)
        self.create_install_cfg(output_dir)

    def create_install_cfg(self, output_dir):
        cfg_file = os.path.join(output_dir, "install.cfg")
        self.writeShellConfigFile(cfg_file)
        print "install.cfg created"

    def writeShellConfigFile(self, filename):
        """Write all of the config file options that we care about to the
        specified file"""
        # How big to make the boot partition for the HD installation image
        boot_partition_size = int(mic_cfg.config.get(self.section, "boot_partition_size"))
        # Options for swap partition: 0. No swap 1. swap always off 2. swap always on
        swap_option = int(mic_cfg.config.get(self.section, "swap_option"))
        # How big to make the swap partition for the HD installation image
        swap_partition_size = int(mic_cfg.config.get(self.section, "swap_partition_size"))
        # How big to make the fat32 partition for the HD installation image
        fat32_partition_size = int(mic_cfg.config.get(self.section, "fat32_partition_size"))
        # Use squashfs or not
        use_squashfs = int(mic_cfg.config.get(self.section, "use_squashfs"))
        if swap_option == 0:
            swap_partition_size = 0
        cfg_dict = {
            'boot_partition_size' : boot_partition_size,
            'swap_option' : swap_option,
            'swap_partition_size' : swap_partition_size,
            'fat32_partition_size' : fat32_partition_size,
            'use_squashfs' : use_squashfs,
        }
        output_file = open(filename, 'w')
        print >> output_file, "#!/bin/bash"
        print >> output_file, "# Dynamically generated config file"
        for key, value in sorted(cfg_dict.iteritems()):
           print >> output_file, "%s=%s" % (key, value)
        output_file.close()

    def create_all_initramfs(self):
        self.kernels.insert(0, self.default_kernel)
        for count, kernel in enumerate(self.kernels):
            kernel_version = kernel.split('vmlinuz-').pop().strip()
            self.create_initramfs("/tmp/.tmp.initrd%d" % count, kernel_version)
        self.kernels.pop(0)

    def create_initramfs(self, initrd_file, kernel_version):
        print "Creating initramfs for kernel version: %s" % kernel_version
        # copy the platform initramfs stuff into /etc/initramfs-tools/ in the target
        src_path = os.path.join('/usr/share/pdk/platforms', self.project.platform.name, 'initramfs')
        dst_path = os.path.join(self.target.fs_path, 'etc', 'initramfs-tools', )
        pdk_utils.rmtree(dst_path, True, callback = self.progress_callback)
        shutil.copytree(src_path, dst_path, True)
        # Create our config file that is used by our scripts during the running
        # of initramfs.  The initramfs/hooks/mobile script in each platform
        # takes care of putting this file into place into the initramfs image.
        cfg_filename = os.path.join(dst_path, "moblin-initramfs.cfg")
        self.writeShellConfigFile(cfg_filename)
        print "moblin-initramfs.cfg file created"
        kernel_mod_path = os.path.join('/lib/modules', kernel_version)
        cmd = "mkinitramfs -o %s %s" % (initrd_file , kernel_mod_path)
        print "Executing: %s" % cmd
        self.target.chroot(cmd)
        
    def create_grub_menu(self):
        print "Creating the grub menu"
        # remove previous menu.lst, since we are about to create one
        menu_dir = os.path.join(self.target.path, "boot/grub")
        menu_file = os.path.join(menu_dir, "menu.lst")
        if os.path.exists(menu_file):
            os.unlink(menu_file)
        if not os.path.exists(menu_dir):
            os.makedirs(menu_dir)
        self.target.chroot("update-grub -y")
        # FIXME: JLV: I really don't like all this sed usage, need to clean this up
        self.target.chroot("/bin/sed s+/boot/+/+g -i /boot/grub/menu.lst")
        menu=open(os.path.join(self.target.fs_path,"boot","grub","menu.lst"),'r')
        for count, line in enumerate(menu):
            if line.find('title') == 0:
                print line
                if line.find(self.default_kernel.split('vmlinuz-').pop().strip()) > 0:
                    # FIXME: JLV: I really don't like all this sed usage, need to clean this up
                    cmd="sed s/^default.*/default\\t\\t%d/g -i /boot/grub/menu.lst" % count
                    print cmd
                    self.target.chroot(cmd)
                    break;
        menu.close()

    def __str__(self):
        return ("<InstallImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))

    def write_manifest(self, image_path):
        all_packages = []
        self.target.chroot("dpkg-query --show", output = all_packages)
        manifest = open(image_path.rstrip('.img') + '.manifest', 'w')
        print >>manifest, "\n".join(all_packages)
        manifest.close()


class LiveIsoImage(InstallImage):
    def install_kernels(self, message_color, message):
        InstallImage.install_kernels(self, 'isolinux.cfg', message_color, message, 'CDImage')

    def create_image(self, fs_type='RAMFS'):
        print "LiveCDImage: Creating Live CD Image(%s) Now..." % fs_type
        image_type = "Live CD Image (no persistent R/W)"
        self.create_all_initramfs()
        self.create_rootfs()
        initrd_stat_result = os.stat('/tmp/.tmp.initrd0')
        rootfs_stat_result = os.stat(self.rootfs_path)

        self.tmp_path = tempfile.mkdtemp('','pdk-', '/tmp')

        self.kernels.insert(0,self.default_kernel)
        for count, kernel in enumerate(self.kernels):
            initrd_path = os.path.join(self.tmp_path, "initrd%d.img" % count)
            shutil.move("/tmp/.tmp.initrd%d" % count, initrd_path)
        self.kernels.pop(0)
        # Flashing yellow on a blue background
        self.install_kernels("9e", image_type)
        pdk_utils.copy(self.rootfs_path, self.tmp_path, callback = self.progress_callback)
        pdk_utils.copy("/usr/lib/syslinux/isolinux.bin", self.tmp_path, callback = self.progress_callback)

        print "Creating CD image file at: %s" % self.path
        cmd_line = "genisoimage -quiet -o %s -b isolinux.bin -c boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -l -R -r %s" % (self.path, self.tmp_path)
        result = pdk_utils.execCommand(cmd_line, callback = self.progress_callback)
        if result:
            print >> sys.stderr, "Error running command: %s" % cmd_line
            raise EnvironmentError, "Error running command: %s" % cmd_line

        shutil.rmtree(self.tmp_path)
        self.tmp_path = ''

        self.delete_rootfs()
        print "LiveIsoImage: Finished!"
        
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
    def install_kernels(self, message_color, message):
        InstallImage.install_kernels(self, 'syslinux.cfg', message_color, message)
        
    def create_usb_image(self, size):
        print "Creating USB flash drive image file at: %s" % self.path
        out_file = open(self.path, 'w')
        # Make a kibibyte length string of zeroes
        out_string = chr(0) * 1024
        # Write the string out to the file to create file of size * mibibyte in length
        for count in range(0, size * 1024):
            if self.progress_callback and count % 1024 == 0:
                self.progress_callback(None)
            out_file.write(out_string)
        out_file.close()

        cmd_line = "mkfs.vfat %s" % self.path
        result = pdk_utils.execCommand(cmd_line, callback = self.progress_callback)
        if result:
            print >> sys.stderr, "Error running command: %s" % cmd_line
            raise EnvironmentError, "Error running command: %s" % cmd_line

        # NOTE: Running syslinux on the host development system
        #       means the host and target have compatible architectures.
        #       This runs syslinux inside the jailroot so the correct
        #       version of syslinux is used.
        jail_path = self.path[len(self.project.path):]
        self.project.chroot('syslinux %s' % jail_path)

    def create_ext3fs_file(self, path, size):
        """Create a ext3fs file.  size is how big to make the file in megabytes"""
        out_file = open(path, 'w')
        out_string = chr(0) * 1024
        for count in range(0, size * 1024):
            out_file.write(out_string)
        out_file.close()

        cmd_line = "mkfs.ext3 %s -F" % path
        result = pdk_utils.execCommand(cmd_line, callback = self.progress_callback)
        if result:
            print >> sys.stderr, "Error running command: %s" % cmd_line
            raise EnvironmentError, "Error running command: %s" % cmd_line

    def mount_container(self):
        if not self.tmp_path:
            self.tmp_path = tempfile.mkdtemp('','pdk-', '/tmp')
            cmd_line = "mount -o loop -t vfat %s %s" % (self.path, self.tmp_path)
            result = pdk_utils.execCommand(cmd_line, callback = self.progress_callback)
            if result:
                print >> sys.stderr, "Error running command: %s" % cmd_line
                raise EnvironmentError, "Error running command: %s" % cmd_line

    def umount_container(self):
        if self.tmp_path:
            result = pdk_utils.umount(self.tmp_path)
            if not result:
                print >> sys.stderr, "Error unmounting: %s" % self.tmp_path
                raise EnvironmentError, "Error unmounting: %s" % self.tmp_path
            os.rmdir(self.tmp_path)
            self.tmp_path = ''

class LiveUsbImage(BaseUsbImage):
    def create_image(self, fs_type='RAMFS'):
        if fs_type == 'EXT3FS':
            print "LiveUsbImage: Creating Live R/W USB Image(%s) Now..." % fs_type
            image_type = "Live R/W USB Image"
        else:
            print "LiveUsbImage: Creating Live USB Image(%s) Now..." % fs_type
            image_type = "Live USB Image (no persistent R/W)"
        # How big to make the ext3 File System on the Live RW USB image, in megabytes
        ext3fs_fs_size = int(mic_cfg.config.get(self.section, "ext3fs_size"))
        self.create_all_initramfs()
        self.create_rootfs()
        initrd_stat_result = os.stat('/tmp/.tmp.initrd0')
        rootfs_stat_result = os.stat(self.rootfs_path)
        size = ((rootfs_stat_result.st_size + initrd_stat_result.st_size) / (1024 * 1024)) + 64
        if fs_type == 'EXT3FS':
           size = size + ext3fs_fs_size
        self.create_usb_image(size)
        self.mount_container()
        self.kernels.insert(0,self.default_kernel)
        for count, kernel in enumerate(self.kernels):
            initrd_path = os.path.join(self.tmp_path, "initrd%d.img" % count)
            shutil.move("/tmp/.tmp.initrd%d" % count, initrd_path)
        self.kernels.pop(0)
        # Flashing yellow on a blue background
        self.install_kernels("9e", image_type)
        pdk_utils.copy(self.rootfs_path, self.tmp_path, callback = self.progress_callback)
        if fs_type == 'EXT3FS':
            self.create_ext3fs_file(os.path.join(self.tmp_path, 'ext3fs.img'), ext3fs_fs_size)
        self.umount_container()
        self.delete_rootfs()
        print "LiveUsbImage: Finished!"
        
    def __str__(self):
        return ("<LiveUsbImage: project=%s, target=%s, name=%s>"
                % (self.project, self.target, self.name))


class InstallUsbImage(BaseUsbImage):
    def create_image(self):
        print "InstallUsbImage: Creating InstallUSB Image..."
        image_type = "Install USB Image.  This will DESTROY all content on your hard drive!!"
        self.create_all_initramfs()
        self.create_grub_menu()
        self.apply_hd_kernel_cmdline()
        self.create_bootfs()
        self.create_rootfs()
        initrd_stat_result = os.stat('/tmp/.tmp.initrd0')
        rootfs_stat_result = os.stat(self.rootfs_path)
        bootfs_stat_result = os.stat(self.bootfs_path)
        size = ((rootfs_stat_result.st_size + bootfs_stat_result.st_size + initrd_stat_result.st_size) / (1024 * 1024)) + 64
        self.create_usb_image(size)
        self.mount_container()
        self.kernels.insert(0,self.default_kernel)
        for count, kernel in enumerate(self.kernels):
            initrd_path = os.path.join(self.tmp_path, "initrd%d.img" % count)
            shutil.move("/tmp/.tmp.initrd%d" % count, initrd_path)
        self.kernels.pop(0)
        # Flashing yellow on a red background
        self.install_kernels("ce", image_type)
        pdk_utils.copy(self.rootfs_path, self.tmp_path, callback = self.progress_callback)
        pdk_utils.copy(self.bootfs_path, self.tmp_path, callback = self.progress_callback)
        self.create_install_script(self.tmp_path)
        self.umount_container()
        self.delete_rootfs()
        self.delete_bootfs()
        print "InstallUsbImage: Finished!"
        print "\nYou can now use the image to boot and install the target file-system on the target device's HDD.\n"
        print "\nWARNING: Entire contents of the target devices's HDD will be erased prior to installation!"
        print "         This includes ALL partitions on the disk!\n"
        print "InstallUsbImage: Finished!"
        
    def apply_hd_kernel_cmdline(self):
        cmd = "sed -e 's:^\\s*kernel\\s*\\([/a-zA-Z0-9._-]*\\).*:kernel \\t\\t\\1 %s:g' -i %s" % (self.project.get_target_hd_kernel_cmdline(self.target.name), os.path.join(self.target.fs_path, 'boot', 'grub', 'menu.lst'))
        print cmd
        print os.popen(cmd).readlines()
        print "grub.conf kernel cmdline changed"

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
    def iteration(self, process):
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
