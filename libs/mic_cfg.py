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
import platform
import pwd
import re
import sys

from ConfigParser import SafeConfigParser

config = None
DEFAULT_CONFIG_DIR = os.path.expanduser("/usr/share/pdk/default_config/")
CONFIG_DIR = os.path.expanduser("~/.image-creator")
# List of valid sections for our config file
BASE_SECTIONS = [ "platform", "installimage", "distribution" ]
VALID_SECTIONS = BASE_SECTIONS + [ "general" ]

# Default values
DEFAULTS = [
    ('general', 'var_dir', '/var/lib/moblin-image-creator'),
    ]


def main():
    # We will print out the configuration as a debugging aid
    readConfig()
    for section in sorted(config.sections()):
        print "[%s]" % section
        for option in config.options(section):
            value = config.get(section, option)
            print "%s=%s" % (option, value)
        print
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
    addDefaults()
    for filename in sorted(os.listdir(DEFAULT_CONFIG_DIR)):
        full_name = os.path.join(DEFAULT_CONFIG_DIR, filename)
        config.read(full_name)
        verifyConfig(full_name)
    user_config_file = os.path.join(CONFIG_DIR, "image-creator.cfg")
    if os.path.isfile(user_config_file):
        config.read(user_config_file)
        verifyConfig(user_config_file)
    fixupConfig()
    addUserInfo()

def verifyConfig(filename):
    """Make sure that we don't have any unknown sections in the config file"""
    for section in config.sections():
        result = re.search(r'^(.*)\.', section)
        if result:
            section = result.group(1)
            if section not in BASE_SECTIONS:
                print "Invalid section: %s" % section
                print "Found in file: %s" % filename
                sys.exit(1)
            continue
        if section not in VALID_SECTIONS:
            print "Invalid section: %s" % section
            print "Found in file: %s" % filename
            sys.exit(1)

def fixupConfig():
    """This takes care of fixing up the config data.  Main thing it does right
    now is fix up stuff for 'platform.platformname' sections"""
    for base_section in BASE_SECTIONS:
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

def addUserInfo():
    # Try to figure out if we have been invoked via sudo
    sudo = 0
    if os.getuid() == 0:
        # our user ID is root, so we may have been invoked via sudo
        if 'SUDO_USER' in os.environ:
            username = os.environ['SUDO_USER']
            sudo = 1
        elif 'USER' in os.environ:
            username = os.environ['USER']
        else:
            username = "root"
    else:
        if 'USER' in os.environ:
            username = os.environ['USER']
        else:
            username = pwd.getpwuid(os.getuid()).pw_name
    #Try to get uid and gid from the user name, which may not exist
    try:
        pwd.getpwnam(username)
    except KeyError:
        username = 'root'

    userid = pwd.getpwnam(username).pw_uid
    groupid = pwd.getpwnam(username).pw_gid
    config.add_section('userinfo')
    config.set('userinfo', 'groupid', "%s" % groupid)
    config.set('userinfo', 'user', username)
    config.set('userinfo', 'userid', "%s" % userid)
    config.set('userinfo', 'sudo', "%s" % sudo)

def addDefaults():
    for section, option, value in DEFAULTS:
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, value)
    # What distribution are we running on
    dist = platform.dist()[0]
    config.set('general', 'distribution', dist)
    if dist == "debian":
        pkg_manager = "apt"
    elif dist == "fedora":
        pkg_manager = "yum"
    else:
        pkg_manager = "unsupported distribution"
    config.set('general', 'package_manager', pkg_manager)

if '__main__' == __name__:
    sys.exit(main())
else:
    readConfig()
