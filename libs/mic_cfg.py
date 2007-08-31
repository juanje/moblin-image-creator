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

    user_config_file = os.path.join(CONFIG_DIR, "image-creator.cfg")
    # FIXME: This is temporary to help out people
    old_config = os.path.join(CONFIG_DIR, "platforms.cfg")
    if os.path.exists(old_config):
        print "Error: The file: %s exists" % old_config
        print "This file is no longer used.  Please convert it over to the new file and then delete it"
        print "Please create a: %s file" % user_config_file
        print "And set it up like the file: %s" % os.path.join(DEFAULT_CONFIG_DIR, "defaults.cfg")
        sys.exit(1)

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
    now is fix up stuff for 'bootstrap.platformname' sections"""
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

if '__main__' == __name__:
    sys.exit(main())
else:
    readConfig()
