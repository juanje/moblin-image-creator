#!/usr/bin/python -tt

import os, sys, re

class Busybox:
    def __init__(self, cmd_path, bin_path):
        self.cmd_path = os.path.abspath(os.path.expanduser(cmd_path))
        self.bin_path = os.path.abspath(os.path.expanduser(bin_path))
        self.cmds = []

        # Extract the list of supported busybox commands
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

        if not os.path.exists("busybox"):
            cmd_string = "/bin/cp %s ." % self.cmd_path
            os.system(cmd_string)

        for cmd in self.cmds:
            if not os.path.exists(cmd):
                os.symlink("busybox", cmd)

        os.chdir(save_cwd)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >> sys.stderr, "USAGE: %s cmd_path bin_path" % (sys.argv[0])
        sys.exit(1)

    b = Busybox(sys.argv[1], sys.argv[2])
    b.create()

#        os.chdir("..")
#        os.system("find -print | cpio -o | gzip -c > /tmp/rob.initrd")
