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

# This file contains a ConfigClass, that will contain our config information.

from ConfigParser import SafeConfigParser

class ConfigClass(object):
    """Class to hold configuration variables as key/value pairs.  Also allows
    additional storage of a description"""
    def __init__(self, input_list = None):
        self.config_dict = {}
        self.protectedkeys = self.__dict__.keys()
        if input_list == None:
            return
        self.setAttributesWithDescription(input_list)

    def setKeyValue(self, key, value, description = None):
        """Set class attributes for the key/value given"""
        if key in self.protectedkeys:
            print "Not allowed to override built in functions: %s" % key
            raise KeyError
        self.config_dict[key] = ConfigChild(value, description)

    def setAttributes(self, input_dict):
        """Given a dictionary, setup the key/values"""
        for key, value in input_dict.items():
            self.setKeyValue(key, value)

    def setAttributesWithDescription(self, input_list):
        """Given a list, with key/value/description items, setup the
        key/value/description"""
        for key, value, description in input_list:
            self.setKeyValue(key, value, description)

    def __getattr__(self, key):
        if key not in self.config_dict:
            print "Key not found: %s" % key
            raise KeyError
        return self.config_dict[key].value

    def get(self, key):
        return self.config_dict[key]

    def __getitem__(self, key):
        return self.__getattr__(key)

    def pformat(self, tabcount = 0):
        """This is kind of funky.  Not sure if I am going to keep it"""
        tabsize = 4
        tabstring1 = " " * (tabsize * tabcount)
        tabstring2 = " " * (tabsize * (tabcount+1))
        tabstring3 = " " * (tabsize * (tabcount+2))
        output = []
        output.append("%sConfigClass([" % tabstring1)
        for key in sorted(self.config_dict):
            value, description = self.config_dict[key]
            if description == None:
                desc = "None"
            else:
                desc = "'%s'" % description
            if type(value) != type(self):
                output.append("%s('%s', '%s', %s)," % (tabstring2, key, value, desc))
            else:
                output.append("%s('%s'," % (tabstring2, key))
                output.extend(value.pformat(tabcount = tabcount + 2))
                output.append("%s%s" % (tabstring3, desc))
                output.append("%s)," % (tabstring2))
        endstring = "%s])" % (tabstring1)
        if tabcount > 0:
            endstring += ","
        output.append(endstring)
        return output

    def writeIniFile(self, filename):
        parser = SafeConfigParser()
        for key in sorted(self.config_dict):
            print key
            parser.add_section(key)
            print self.config_dict[key]
            print

    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        output = []
        for key in sorted(self.config_dict):
            output.append( (key, self.config_dict[key].__repr__() ) )
        return "ConfigClass(%s)" % output

class ConfigChild(object):
    __slots__ = 'value', 'description'  # try to minimize space used
    def __init__(self, value, description = None):
        if isinstance(value, ConfigChild):
            # We do not allow ConfigChild objects to store another ConfigChild
            # object because we want to be able to store the config in a normal
            # INI formatted file.
            print "Not allowed to store a ConfigChild object inside a ConfigChild object"
            print "Tried to store: %s" % value
            raise ValueError
        if isinstance(value, ConfigClass):
            # We do not allow ConfigChild objects to store a ConfigClass object
            # because we want to be able to store the config in a normal INI
            # formatted file.
            print "Not allowed to store a ConfigClass object inside a ConfigChild object"
            print "Tried to store: %s" % value
            raise ValueError
        self.value = value
        self.description = description

    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return "ConfigChild('%s', %s)" % (self.value, self.description)
