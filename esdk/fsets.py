#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import ConfigParser, os, re, sys, unittest

class FSet(object):
    """
    An FSet object represents a functional set of packages to install in a
    target filesystem.  An FSet contains an array of package names in
    FSet.packages, an array of additional debug packages in
    FSet.debug_packages, and an array of dependant FSet names in FSet.deps.
    """
    def __init__(self):
        self.filenames = []
        self.__fsets = {}

    def addFile(self, filename):
        """Add a config file to the FSet"""
        filename = os.path.abspath(os.path.expanduser(filename))
        self.filenames.append(filename)
        self.__parseFile(filename)


    def __parseFile(self, filename):
        valid_values = { 'desc' : '', 'pkgs' : [], 'debug_pkgs' : [],
            'deps' : [] }
        p = ConfigParser.ConfigParser()
        filenames = p.read(filename)
        for section in p.sections():
            orig_section = section
            section = section.lower()
            if section in self.__fsets:
                raise ValueError, "Error: Already have a section called: %s" % section
            work_dict = {}
            work_dict['filename'] = filename
            fset = FsetInstance(section)
            for name, value in p.items(orig_section):
                fset.add(name, value)
            self.__fsets[section] = fset

    def __getitem__(self, key):
        return self.__fsets[key.lower()]
    def __iter__(self):
        return self.__fsets.__iter__()
    def iterkeys(self):
        return self.__fsets.iterkeys()
    def __len__(self):
        return len(self.__fsets)
    def __str__(self):
        return ('<data="%s">'
                % (self.__fsets))
    def __repr__(self):
        return "FSet()"

class FsetInstance(object):
    valid_values = { 'desc' : '', 'pkgs' : [], 'debug_pkgs' : [], 'deps' : [] }
    def __init__(self, name):
        self.name = name.lower()
        self.data = {}
    def add(self, key, value):
        key = key.lower()
        if key not in FsetInstance.valid_values:
            print "Found unsupported value, ignoring: %s = %s" % (key, value)
            return
        work_type = type(FsetInstance.valid_values[key])
        if work_type == type([]):
            value = value.split()
        elif work_type == type(''):
            pass
        else:
            print "Error: Unsupported type specified in FsetInstance.valid_values"
            print "Type was: %s" % work_type
            raise ValueError
        self.data[key] = value
    def get(self, key):
        key = key.lower()
        if key not in FsetInstance.valid_values:
            raise KeyError
        if key in self.data:
            return self.data[key]
        else:
            return FsetInstance.valid_values[key]
    def __getitem__(self, key):
        return self.get(key)
    def __getattr__(self, key):
        return self.get(key)
    def __repr__(self):
        return ('FsetInstance("%s", %s)' % (self.name, self.data))
    def __str__(self):
        return ('<fset name="%s" data="%s">' % (self.name, self.data))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print >> sys.stderr, "USAGE: %s FSET_FILE ..." % (sys.argv[0])
    else:
        fset = FSet()
        for filename in sys.argv[1:]:
            fset.addFile(filename)
        print fset
        for key in fset.fsets:
            print
            print key, fset[key]
            print fset[key].filename, fset[key]['filename']
