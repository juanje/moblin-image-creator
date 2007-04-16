#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

# This file contains utility functions which do not need to be inside any of
# our current classes

import os
import re
import sys

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

if '__main__' == __name__:
    sys.exit(main())
