#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, sys, re, tempfile, shutil

import SDK

class Busybox(object):
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
                # Delete all spaces inside the line
                line = re.sub(r'\s+', '', line)

                if line:
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
                os.link("busybox", cmd)

        os.chdir(save_cwd)

def create(project, initrd_file):
    """Function to create an initrd file"""
    initrd_file = os.path.abspath(os.path.expanduser(initrd_file))

    save_cwd = os.getcwd()
    # Create scratch area for creating files
    scratch_path = tempfile.mkdtemp('','esdk-', '/tmp')

    # Setup initrd directory tree
    bin_path = os.path.join(scratch_path, 'bin')

    # Create directories
    dirs = [ 'bin', 'boot', 'etc', 'dev', 'lib', 'mnt', \
             'proc', 'sys', 'sysroot', 'tmp', ]
    for dirname in dirs:
        os.makedirs(os.path.join(scratch_path, dirname))

    os.symlink('init', os.path.join(scratch_path, 'linuxrc'))
    os.symlink('bin', os.path.join(scratch_path, 'sbin'))

    # Setup Busybox in the initrd
    cmd_path = os.path.join(project.path, 'sbin/busybox')
    bb = Busybox(cmd_path, bin_path)
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
mdev -s
mknod /dev/sda b 8 0
mknod /dev/sda1 b 8 1
mknod /dev/sda2 b 8 2
mknod /dev/sda3 b 8 3
mknod /dev/sdb b 8 16
echo Mounting rootfs
mkdir /newroot
sleep 15
mount -t vfat /dev/sda /newroot
cd /newroot
mkdir initrd
pivot_root . initrd
/bin/msh
"""
    init_file.close()
    os.chmod(os.path.join(scratch_path, 'init'), 0755)

    # Create the initrd image file
    os.chdir(scratch_path)
    cmd_string = "find -print | cpio --quiet -c -o | gzip -9 -c > " + initrd_file
    os.system(cmd_string)
    os.chdir(save_cwd)

    # Clean-up and remove scratch area
    shutil.rmtree(scratch_path)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >> sys.stderr, "USAGE: %s PROJECT INITRD_FILE" % (sys.argv[0])
        sys.exit(1)

    project_name = sys.argv[1]
    initrd_file = sys.argv[2]

    proj = SDK.SDK().projects[project_name]

    create(proj, initrd_file)
