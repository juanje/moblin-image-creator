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
import sys

from ConfigParser import SafeConfigParser

config = None
DEFAULT_CONFIG_DIR = os.path.expanduser("/usr/share/pdk/default_config/")
CONFIG_DIR = os.path.expanduser("~/.image-creator")

def main():
    readConfig()
    for section in config.sections():
        print "[%s]" % section
        for option in config.options(section):
            value = config.get(section, option)
            print "%s=%s" % (option, value)
    return

def configDir():
    return CONFIG_DIR

def readConfig():
    if not os.path.isdir(CONFIG_DIR):
        print "~/.image-creator/ directory did not exist.  Creating"
        os.makedirs(CONFIG_DIR)
    global config
    config = SafeConfigParser()
    for filename in sorted(os.listdir(DEFAULT_CONFIG_DIR)):
        full_name = os.path.join(DEFAULT_CONFIG_DIR, filename)
        config.read(full_name)
    user_config_file = os.path.join(CONFIG_DIR, "image-creator.cfg")
    if os.path.isfile(user_config_file):
        config.read(user_config_file)
    fixupConfig()

def fixupConfig():
    """This takes care of fixing up the config data.  Main thing it does right
    now is fix up stuff for 'buildroot.platformname' sections"""
    base_sections = [ "bootstrap" ]
    for base_section in base_sections:
        # If we don't have the base section, then we know we will not copy
        # anything over
        if not config.has_section(base_section):
            continue
        for custom_section in config.sections():
            # See if we have a custom section
            if re.search(base_section + r'\.', custom_section):
                for option in config.options(base_section):
                    if not config.has_option(custom_section, option):
                        value = config.get(base_section, option)
                        config.set(custom_section, option, value)

def print_exc_plus(type, value, tb):
    # From Python Cookbook 2nd Edition.  FIXME: Will need to remove this at
    # some point, or give attribution.
    # This is a modified version of recipe 8.6
    """ Print the usual traceback information, followed by a listing of
        all the local variables in each frame.
    """
    while tb.tb_next:
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    traceback.print_exception(type, value, tb)
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
    traceback.print_exception(type, value, tb)


if '__main__' == __name__:
    sys.exit(main())
else:
    readConfig()
