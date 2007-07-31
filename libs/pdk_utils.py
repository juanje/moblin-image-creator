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

import os
import re
import select
import subprocess
import sys

# this is for the copySourcesListFile() function
src_regex = None
if os.path.isdir(os.path.expanduser("~/.image-creator")):
    sources_regex_file = os.path.expanduser("~/.image-creator/sources_cfg")
    if os.path.isfile(sources_regex_file):
        global_dict = {}
        try:
            execfile(sources_regex_file, global_dict)
            if 'sources_regex' in global_dict:
                src_regex = global_dict['sources_regex']
        except:
            pass

def main():
    # Add something to exercise this code
    print "USB devices: %s" % get_current_udisks()

def get_current_udisks():
    usb_devices = []
    dirname = os.path.abspath('/sys/bus/scsi')
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
    search_file = "%s " % os.path.abspath(device_file)
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

def ismount(path):
    """Function to see if a path is mounted, this is because os.path.ismount()
    does not seem to detect --bind"""
    path = os.path.abspath(os.path.expanduser(path))
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

def execCommand(cmd_line, quiet = False, output = None, callback = None):
        if output == None:
            p = subprocess.Popen(cmd_line.split())
        else:
            p = subprocess.Popen(cmd_line.split(), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, stdin = subprocess.PIPE, close_fds = True)
        # Don't ever want the process waiting on stdin.
        if output != None:
            p.stdin.close()
        # This is so that we can keep calling our callback
        pl = select.poll()
        if output != None:
            pl.register(p.stdout)
        while p.poll() == None:
            if output != None and pl.poll(10):
                line = p.stdout.readline()
                line = line.rstrip()
                output.append(line)
                if not quiet:
                    print line
            elif callback:
                callback(p)
        if output != None:
            # Now check if any output is left over
            for line in p.stdout.readlines():
                line = line.rstrip()
                output.append(line)
                if not quiet:
                    print line
        result = p.returncode
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


if '__main__' == __name__:
    sys.exit(main())
