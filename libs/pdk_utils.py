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

# This file contains utility functions which do not need to be inside any of
# our current classes

import exceptions
import fcntl
import os
import re
import select
import subprocess
import sys

# this is for the copySourcesListFile() function
src_regex = None
CONFIG_DIR = os.path.expanduser("~/.image-creator")
if not os.path.isdir(CONFIG_DIR):
    print "~/.image-creator/ directory did not exist.  Creating"
    os.makedirs(CONFIG_DIR)

sources_regex_file = os.path.expanduser(os.path.join(CONFIG_DIR, "sources_cfg"))
if os.path.isfile(sources_regex_file):
    global_dict = {}
    execfile(sources_regex_file, global_dict)
    if 'sources_regex' in global_dict:
        src_regex = global_dict['sources_regex']
else:
    print "Creating sample %s file" % sources_regex_file
    out_file = open(sources_regex_file, 'w')
    print  >> out_file, """#!/usr/bin/python

# If you have a local mirror of the Ubuntu and/or Moblin.org APT repositories,
# then this configuration file will be useful to you.

# This file is used when copying the files that will go into
# /etc/apt/sources.list.d/  It consists of a list, which contains a search
# regular expression and a replacement string.  When copying the files into the
# /etc/apt/sources.list.d/ , of the projects and targets, a search and replace
# will be performed.

sources_regex = [
    # source_archive,                           local mirror of source archive

# Edit the following and uncomment them to enable use of a local mirror server.
#    (r'http://ports.ubuntu.com/ubuntu-ports gutsy', 'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_PORTS_UBUNTU_COM/ gutsy'),
#    (r'http://www.moblin.org/apt gaston',       'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_MOBLIN_ORG/ gaston'),

]"""
    out_file.close()

def main():
    # Add something to exercise this code
    print "USB devices: %s" % get_current_udisks()

def get_current_udisks():
    usb_devices = []
    dirname = os.path.realpath(os.path.abspath('/sys/bus/scsi'))
    work_list = getUsbDirTree(dirname)
    usb_list = [ x for x in work_list if re.search(r'usb', x) ]
    for filename in usb_list:
        device_dir = os.path.join('/sys/devices', filename)
        if os.path.isdir(device_dir):
            for device_file in os.listdir(device_dir):
                full_path = os.path.join(device_dir, device_file)
                result = re.search(r'^block:(?P<dev>.*)', device_file)
                if result:
                    usb_dev = os.path.join('/dev', result.group('dev'))
                    if os.path.exists(usb_dev):
                        usb_devices.append(usb_dev)
    return usb_devices

def getUsbDirTree(dirname):
    file_set = set()
    for filename in os.listdir(dirname):
        full_path = os.path.join(dirname, filename)
        if os.path.islink(full_path):
            file_set.add(os.path.realpath(full_path))
        elif os.path.isdir(full_path):
            file_set.update(getUsbDirTree(full_path))
        else:
            file_set.add(full_path)
    return file_set

def umount_device(device_file):
    """umount a device if it is mounted"""
    search_file = "%s " % os.path.realpath(os.path.abspath(device_file))
    mount_file = open('/proc/mounts', 'r')
    for line in mount_file:
        line = line.strip()
        if line.find(search_file) == 0:
            print "Umounting: %s" % device_file
            result = os.system("umount %s" % device_file)
            if result:
                return False
            return True
    return True

def getMountInfo():
    """Function to parse the list of mounts and return back the data"""
    output = {}
    mounts_file = "/proc/mounts"
    in_file = open(mounts_file, 'r')
    for line in in_file:
        line = line.strip()
        mount_info = MountInfo(line)
        output[mount_info.dirname] = mount_info
    return output

def ismount(path):
    """Function to see if a path is mounted, this is because os.path.ismount()
    does not seem to detect --bind"""
    path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
    output = []
    cmd = "mount"
    result = execCommand(cmd, quiet = True, output = output)
    for line in output:
        result = re.search(r'(?P<dev>.*) on (?P<mnt_point>.*) type', line)
        if result:
            mnt_point = result.group('mnt_point')
            if mnt_point == path:
                return True
    return False


def setblocking(f, flag):
    " set/clear blocking mode"
    # get the file descriptor
    fd = f.fileno()
    # get the file's current flag settings
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    if flag:
        # clear non-blocking mode from flags
        fl = fl & ~os.O_NONBLOCK
    else:
        # set non-blocking mode from flags
        fl = fl | os.O_NONBLOCK
    # update the file's flags
    fcntl.fcntl(fd, fcntl.F_SETFL, fl)

def execCommand(cmd_line, quiet = False, output = None, callback = None):
        if output == None and callback == None:
            p = subprocess.Popen(cmd_line.split())
        else:
            p = subprocess.Popen(cmd_line.split(), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, stdin = subprocess.PIPE, close_fds = True)
        # To get the callbacks to work, we need to capture the output
        if callback != None and output == None:
            output = []
        # Don't ever want the process waiting on stdin.
        if output != None:
            p.stdin.close()
            # Make the stdout of the subprocess non-blocking, so that we won't
            # ever hang waiting for it.  This way our callback function should
            # always keep being called.
            setblocking(p.stdout, False)
        # This is so that we can keep calling our callback
        poll = select.poll()
        if output != None:
            poll.register(p.stdout, select.POLLIN)
        out_buffer = ""
        # As long as our subprocess returns None, then the subprocess is still
        # running.
        while p.poll() == None:
            if output != None:
                # Only do this if we are capturing output
                result = poll.poll(10)
                if result:
                    buf = p.stdout.read()
                    if buf != "":
                        out_buffer += buf
                        if not quiet:
                            sys.stdout.write(buf)
            if callback:
                callback(p)
        if output != None:
            # Have to scan for anything remaining in the subprocess stdout
            # buffer
            while True:
                buf = p.stdout.read()
                if buf == "":
                    break
                out_buffer += buf
                if not quiet:
                    sys.stdout.write(buf)
            # Now we have to package up our output
            for line in out_buffer.splitlines():
                output.append(line)
        result = p.returncode
        return result

def execChrootCommand(path, cmd, output = None, callback = None):
    if not os.path.isfile(os.path.join(path, 'bin/bash')):
        print >> sys.stderr, "Incomplete jailroot at %s" % (path)
        raise ValueError("Internal Error: Invalid buildroot at %s" % (path))
    if output == None:
        output = []
    cmd_line = "chroot %s %s" % (path, cmd)
    result = execCommand(cmd_line, output = output, callback = callback)
    if result != 0:
        print "Error in chroot.  Result: %s" % result
        print "Command was: %s" % cmd_line
        sys.stdout.flush()
    return result

def copySourcesListFile(sourcefile, destfile):
    """The purpose of this function is allow the user to be able to point at a
    local repository for some of the sources, rather than going out over the
    Internet"""
    in_file = open(sourcefile, 'r')
    out_file = open(destfile, 'w')
    for line in in_file:
        line=line.strip()
        if type(src_regex) == type([]):
            for regex, sub in src_regex:
                line = re.sub(regex, sub, line)
        print >> out_file, line
    in_file.close()
    out_file.close()

class MountInfo(object):
    def __init__(self, mount_line):
        """Input is in the form that is found in /etc/mtab (or /proc/mounts)"""
        mount_line = mount_line.strip()
        result = mount_line.split()
        self.device = result[0]
        self.dirname = result[1]
        self.fs_type = result[2]
        self.options = result[3]
    def __str__(self):
        return ("%s %s %s %s" % (self.device, self.dirname, self.fs_type, self.options))
    def __repr__(self):
        return "MountInfo('%s')" % self.__str__()


# An exception class for Image Creator
class ImageCreatorError(exceptions.Exception):
    def __init__(self, args=None):
        self.args = args

if '__main__' == __name__:
    sys.exit(main())
