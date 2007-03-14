#!/usr/bin/python -tt

import os, sys, re, tempfile, shutil

class Busybox:
    def __init__(self, cmd_path, bin_path):
        self.cmd_path = os.path.abspath(os.path.expanduser(cmd_path))
        self.bin_path = os.path.abspath(os.path.expanduser(bin_path))
        self.cmds = []

        # Extract the list of supported busybox commands
        #
        # This is far from ideal, but this method doesn't require
        # modifying the original Busybox RPM package and capturing
        # symlinks w/ a "make install" of the Busybox sources
        buf = ""
        flag = 0
        bf = os.popen(cmd_path)
        for line in bf:
            if (flag == 0):
                if re.search(r'^Currently defined functions:', line):
                    flag = 1
                continue
            else:
                # strip off the new-line & white-space
                line = line.strip()
                line = re.sub(r'\s+', '', line)

                if (line != ''):
                    buf = buf + line

        buf = re.sub(r'busybox,', '', buf)
        self.cmds = buf.split(',')

    def create(self):
        if not os.path.isdir(self.bin_path):
            os.makedirs(self.bin_path)

        save_cwd = os.getcwd()
        os.chdir(self.bin_path)

        if not os.path.exists('busybox'):
            shutil.copy(self.cmd_path, 'busybox')

        for cmd in self.cmds:
            if not os.path.exists(cmd):
                os.symlink("busybox", cmd)

        os.chdir(save_cwd)

class Mkinitrd:
    def __init__(self, initrd_file):
        self.initrd_file = os.path.abspath(os.path.expanduser(initrd_file))

    def create(self):
        save_cwd = os.getcwd()

        # Create scratch area for creating files
        scratch_path = tempfile.mkdtemp('','esdk-', '/tmp')

        # Setup initrd directory tree
        bin_path = os.path.join(scratch_path, 'bin')

        os.makedirs(bin_path)
        os.makedirs(os.path.join(scratch_path, 'etc'))
        os.makedirs(os.path.join(scratch_path, 'dev'))
        os.makedirs(os.path.join(scratch_path, 'lib'))
        os.symlink('init', os.path.join(scratch_path, 'linuxrc'))
        os.makedirs(os.path.join(scratch_path, 'proc'))
        os.symlink('bin', os.path.join(scratch_path, 'sbin'))
        os.makedirs(os.path.join(scratch_path, 'sys'))
        os.makedirs(os.path.join(scratch_path, 'sysroot'))
        os.makedirs(os.path.join(scratch_path, 'tmp'))

        # Setup Busybox in the initrd
        bb = Busybox("/sbin/busybox", bin_path)
        bb.create()

        # Setup init script
        init_file = open(os.path.join(scratch_path, 'init'), 'w')
        print >> init_file, """\
#!/bin/msh

mount -t proc /proc /proc
echo Mounting proc filesystem
echo Mounting sysfs filesystem
mount -t sysfs /sys /sys
echo Creating /tmp
mount -t tmpfs /tmp /tmp
echo Creating /dev
mount -o mode=0755 -t tmpfs /dev /dev
mkdir /dev/pts
mount -t devpts -o gid=5,mode=620 /dev/pts /dev/pts
mkdir /dev/shm
mkdir /dev/mapper
echo Creating initial device nodes
mknod /dev/null c 1 3
mknod /dev/zero c 1 5
mknod /dev/systty c 4 0
mknod /dev/tty c 5 0
mknod /dev/console c 5 1
mknod /dev/ptmx c 5 2
mknod /dev/rtc c 10 135
mknod /dev/sda b 8 0
mknod /dev/sda1 b 8 1
mknod /dev/sda2 b 8 2
mknod /dev/sda3 b 8 3
mknod /dev/tty0 c 4 0
mknod /dev/tty1 c 4 1
mknod /dev/tty2 c 4 2
mknod /dev/tty3 c 4 3
mknod /dev/tty4 c 4 4
mknod /dev/tty5 c 4 5
mknod /dev/tty6 c 4 6
mknod /dev/tty7 c 4 7
mknod /dev/tty8 c 4 8
mknod /dev/tty9 c 4 9
mknod /dev/tty10 c 4 10
mknod /dev/tty11 c 4 11
mknod /dev/tty12 c 4 12
mknod /dev/ttyS0 c 4 64
mknod /dev/ttyS1 c 4 65
mknod /dev/ttyS2 c 4 66
mknod /dev/ttyS3 c 4 67
echo Setting up hotplug.
hotplug
echo Creating block device nodes.
mkblkdevs
#resume LABEL=SWAP-hda3
#echo Creating root device.
#mkrootdev -t ext3 -o defaults,ro hda1
#echo Mounting root filesystem.
#mount /sysroot
#echo Setting up other filesystems.
#setuproot
#echo Switching to new root and running init.
#switchroot
/bin/msh
"""
        init_file.close()
        os.chmod(os.path.join(scratch_path, 'init'), 0755)

        # Create the initrd image file
        os.chdir(scratch_path)
        cmd_string = "find -print | cpio --quiet -c -o | gzip -9 -c > " + self.initrd_file
        os.system(cmd_string)
        os.chdir(save_cwd)

        # Clean-up and remove scratch area
        print scratch_path
        shutil.rmtree(scratch_path)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >> sys.stderr, "USAGE: %s INITRD_FILE" % (sys.argv[0])
        sys.exit(1)

    initrd = Mkinitrd(sys.argv[1])
    initrd.create()
