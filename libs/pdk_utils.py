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
import gobject
import os
import re
import select
import stat
import subprocess
import sys
import tempfile
import shutil
import time

import mic_cfg

# this is for the copySourcesListFile() function
src_regex = None
CONFIG_DIR = os.path.expanduser("~/.image-creator")
if not os.path.isdir(CONFIG_DIR):
    print "~/.image-creator/ directory did not exist.  Creating"
    os.makedirs(CONFIG_DIR)

sources_regex_file = os.path.expanduser(os.path.join(CONFIG_DIR, "sources_cfg"))
if os.path.isfile(sources_regex_file):
    f = open(sources_regex_file, "r")
    mirrorSelectionLine = f.readline()
    f.close()
    global_dict = {}
    execfile(sources_regex_file, global_dict)
    if mirrorSelectionLine.find("=") != -1:
        mirrorToUse = mirrorSelectionLine.split('=')[1]
        mirrorToUse = mirrorToUse[1:-2]
        if mirrorToUse != "no_mirror":
            if mirrorToUse in global_dict:
                src_regex = global_dict[mirrorToUse]
            else:
                if 'sources_regex' in global_dict:
                    src_regex = global_dict['sources_regex']
    else:
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
# NOTE: The trailing space is important in the strings!!!!
#    (r'http://archive.ubuntu.com/ubuntu ',       'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_ARCHIVES_UBUNTU_COM/ '),
#    (r'http://ports.ubuntu.com/ubuntu-ports ', 'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_PORTS_UBUNTU_COM/ '),
#    (r'http://www.moblin.org/apt ',       'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_MOBLIN_ORG/ '),

]"""
    out_file.close()

# Make sure the file and directory are owned by the user if it is currently
# owned by root.
userid = int(mic_cfg.config.get("userinfo", "userid"))
groupid = int(mic_cfg.config.get("userinfo", "groupid"))
for filename in [ CONFIG_DIR, sources_regex_file ]:
    stat_val = os.stat(filename)
    st_uid = stat_val[stat.ST_UID]
    st_gid = stat_val[stat.ST_GID]
    do_chmod = False
    if st_uid == 0 and userid != 0:
        do_chmod = True
    elif st_gid == 0 and groupid != 0:
        do_chmod = True
    if do_chmod:
        os.chown(filename, userid, groupid)

def main():
    # Add something to exercise this code
    print "USB devices: %s" % get_current_udisks()

def areWeRoot():
    """Figure out if we are running as root"""
    sudo = int(mic_cfg.config.get('userinfo', 'sudo'))
    userid = int(mic_cfg.config.get('userinfo', 'userid'))
    if sudo == 0 and userid != 0:
        return False
    return True

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

def umountAllInPath(dirname, directory_set = None):
    """Unmount all mounts that are found underneath the dirname specified.  On
    error returns a set containing the list of directories that failed to
    unmount"""
    # Have to add a '/' on the end to prevent /foo/egg and /foo/egg2 being
    # treated as if both were under /foo/egg
    if directory_set == None:
        directory_set = set()
    our_path = os.path.realpath(os.path.abspath(dirname)) + os.sep
    mounts = getMountInfo()
    for mpoint in mounts:
        fs_type=mounts[mpoint].fs_type
        mpoint = os.path.realpath(os.path.abspath(mpoint)) + os.sep
        if our_path == mpoint[:len(our_path)]:
            # need save tmpfs to 'real' dir
            if fs_type == 'tmpfs':
                tmp_path = tempfile.mkdtemp('','pdk-', '/tmp')
                os.rmdir(tmp_path)
                shutil.copytree(mpoint, tmp_path)
            result = umount(mpoint)
            if not result:
                directory_set.add(os.path.abspath(mpoint))
                if fs_type == 'tmpfs':
                    shutil.rmtree(tmp_path)
            elif fs_type == 'tmpfs':
                os.rmdir(mpoint)
                shutil.move(tmp_path, mpoint)
    return directory_set

def umount(dirname):
    """Helper function to un-mount a directory, returns back False if it failed
    to unmount the directory"""
    dirname = os.path.abspath(os.path.expanduser(dirname))
    result = os.system("umount %s" % (dirname))
    if result:
        # umount failed, see if the directory is actually mounted, if it isn't
        # then we think it is okay
        mounts = getMountInfo()
        if dirname in mounts:
            return False
    return True

def umount_device(device_file):
    """umount a device if it is mounted"""
    search_file = "%s " % os.path.realpath(os.path.abspath(device_file))
    mount_file = open('/proc/mounts', 'r')
    for line in mount_file:
        line = line.strip()
        if line.find(search_file) == 0:
            print "Umounting: %s" % device_file
            return umount(device_file)
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
    cmd_line = "/usr/sbin/chroot %s %s" % (path, cmd)
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
        line = line.strip()
        if type(src_regex) == type([]):
            for regex, sub in src_regex:
                line = re.sub(regex, sub, line)
        print >> out_file, line
    in_file.close()
    out_file.close()

def touchFile(filename):
    """Work like the 'touch' command"""
    if not os.path.exists(filename):
        basedir = os.path.dirname(filename)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        out_file = open(filename, 'w')
        out_file.close()
    os.utime(filename, None)

def rmtree(path, ignore_errors=False, onerror=None, callback = None, count = 0):
    """Recursively delete a directory tree.

    This function was copied from the shutil.py library in Python 2.5.1.  The
    license for Python is GPL compatible so it is okay to use it.  The reason
    for creating a custom version of this is so that we can have a callback
    function.  This way our throbber won't die for long periods of time when
    deleting a large directory tree.

    If ignore_errors is set, errors are ignored; otherwise, if onerror
    is set, it is called to handle the error with arguments (func,
    path, exc_info) where func is os.listdir, os.remove, or os.rmdir;
    path is the argument to that function that caused it to fail; and
    exc_info is a tuple returned by sys.exc_info().  If ignore_errors
    is false and onerror is None, an exception is raised.
    """
    if ignore_errors:
        def onerror(*args):
            pass
    elif onerror is None:
        def onerror(*args):
            raise
    names = []
    try:
        names = os.listdir(path)
    except os.error, err:
        onerror(os.listdir, path, sys.exc_info())
    for name in names:
        count += 1
        # For every 200 files deleted, lets call our callback
        if count % 200 == 0 and callback:
            callback(None)
        fullname = os.path.join(path, name)
        try:
            mode = os.lstat(fullname).st_mode
        except os.error:
            mode = 0
        if stat.S_ISDIR(mode):
            rmtree(fullname, ignore_errors, onerror, callback = callback, count = count)
        else:
            try:
                os.remove(fullname)
            except os.error, err:
                onerror(os.remove, fullname, sys.exc_info())
    try:
        os.rmdir(path)
    except os.error:
        onerror(os.rmdir, path, sys.exc_info())

def copy(src, dst, callback = None):
    if callback:
        timer = gobject.timeout_add(100, callback, None)
        pid = os.fork()
        if (pid == 0):
            # child process
            shutil.copy(src, dst)
            os._exit(0)
        while 1:
            pid, exit_status = os.waitpid(pid, os.WNOHANG)
            if pid == 0:
                callback(None)
                time.sleep(0.1)
            else:
                gobject.source_remove(timer)
                break
            if exit_status:
                # Something failed, try again without the fork
                shutil.copy(src, dst)
    else:
        shutil.copy(src, dst)

def safeTextFileCopy(source_file, destination_file, force = False):
    """Routine which attempts to safely copy a text file.  This means that if
    we have the destination file and it has our signature text in it, then we
    will overwrite it.  But if the signature text is not in the destination
    file then we will not overwrite it"""
    id_string = "# ##-Created by Moblin Image Creator: if this line exists we will overwrite this file -##"
    copyfile = False
    if os.path.isfile(source_file):
        if not os.path.isfile(destination_file) or force:
            copyfile = True
        else:
            in_file = open(destination_file, 'r')
            for line in in_file:
                line = line.strip()
                if re.search(r'^' + id_string, line):
                    copyfile = True
                    break
            in_file.close()
    if copyfile:
        in_file = open(source_file, 'r')
        out_file = open(destination_file, 'w')
        print >> out_file, id_string
        for line in in_file:
            out_file.write(line)
        in_file.close()
        out_file.close()

def mountList(mount_list, chroot_dir):
    """Mount the items specified in the mount list.  Return back a list of what
    got mounted"""
    # We want to keep a list of everything we mount, so that we can use it in
    # the umount portion
    mounted_list = []
    mounts = getMountInfo()
    for mnt_type, host_dirname, target_dirname, fs_type, device in mount_list:
        # If didn't specify target_dirname then use the host_dirname path,
        # but we have to remove the leading '/'
        if not target_dirname and host_dirname:
            target_dirname = re.sub(r'^' + os.sep, '', host_dirname)
        # Do the --bind mount types
        if mnt_type == "bind":
            path = os.path.join(chroot_dir, target_dirname)
            mounted_list.append(path)
            if not os.path.isdir(path):
                os.makedirs(path)
            if not ismount(path) and os.path.isdir(host_dirname):
                result = os.system('mount --bind %s %s' % (host_dirname, path))
                if result != 0:
                    raise OSError("Internal error while attempting to bind mount /%s!" % (host_dirname))
        # Mimic host mounts, if possible
        elif mnt_type == 'host':
            if host_dirname in mounts:
                mount_info = mounts[host_dirname]
                fs_type = mount_info.fs_type
                device = mount_info.device
                options = "-o %s" % mount_info.options
            else:
                options = ""
            path = os.path.join(chroot_dir, target_dirname)
            mounted_list.append(path)
            if not os.path.isdir(path):
                os.makedirs(path)
            if not ismount(path):
                cmd = 'mount %s -t %s %s %s' % (options, fs_type, device, path)
                result = execCommand(cmd)
                if result != 0:
                    raise OSError("Internal error while attempting to mount %s %s!" % (host_dirname, target_dirname))
    return mounted_list

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


class ImageCreatorUmountError(ImageCreatorError):
    def __init__(self, directory_set = set()):
        self.directory_set = directory_set

def getAllProcesses():
    """Return back a dictionary of all the currently running processes on the
    system"""
    processes = {}
    dirname = "/proc"
    for filename in sorted(os.listdir(dirname)):
        full_path = os.path.join(dirname, filename)
        if os.path.isdir(full_path) and re.search(r'^[0-9]+$', filename):
            pid = int(filename)
            in_file = open(os.path.join(full_path, "status"))
            for line in in_file:
                line = line.strip()
                result = re.search(r'^ppid:\t(?P<ppid>.*)', line, re.I)
                if result:
                    ppid = int(result.group('ppid'))
                    processes.setdefault(ppid, []).append(pid)
                    break
            in_file.close()
    return processes

def findChildren(pid, process_dict = None):
    """Find all the children of PID (Process ID).  Does not return back PID"""
    output = []
    if not process_dict:
        process_dict = getAllProcesses()
    if pid in process_dict:
        for child_pid in process_dict[pid]:
            output.append(child_pid)
            output.extend(findChildren(child_pid, process_dict))
    output.sort()
    return output

def signalChildren(pid, send_signal, process_dict = None, parent_first = True):
    """Send the signal 'send_signal' to the parent and all of its children
        parent_first = Send the signal to the parent before signaling the
        children"""
    if not process_dict:
        process_dict = getAllProcesses()
    if pid in process_dict:
        if parent_first:
            print "Sending signal: %s to PID: %s" % (send_signal, pid)
            try:
                os.kill(pid, send_signal)
            except:
                pass
        for child_pid in process_dict[pid]:
            signalChildren(child_pid, send_signal = send_signal,
                process_dict = process_dict, parent_first = parent_first)
        if not parent_first:
            print "Sending signal: %s to PID: %s" % (send_signal, pid)
            try:
                os.kill(pid, send_signal)
            except:
                pass

if '__main__' == __name__:
    sys.exit(main())
