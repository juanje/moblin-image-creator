#!/usr/bin/python -tt

import ConfigParser, os, re, sys

class FSet(object):
    """
    An FSet object represents a functional set of packages to install in a
    target filesystem.  An FSet contains an array of package names in
    FSet.packages, an array of additional debug packages in
    FSet.debug_packages, and an array of dependant FSet names in FSet.deps.
    """
    def __init__(self):
        self.filenames = []
        self.fsets = {}

    def addFile(self, filename):
        """Add a config file to the FSet"""
        filename = os.path.abspath(os.path.expanduser(filename))
        self.filenames.append(filename)
        self.__parseFile(filename)


    def __parseFile(self, filename):
        valid_values = { 'name' : '', 'desc' : '', 'pkgs' : [],
            'debug_pkgs' : [], 'deps' : [] }
        p = ConfigParser.ConfigParser()
        filenames = p.read(filename)
        for section in p.sections():
            orig_section = section
            section = section.lower()
            if section in self.fsets:
                print "Error: Already have a section called: %s" % section
                print "Tried to add the section from file: %s" % filename
                print "But already have that section from file: %s" % self.fsets[section]['filename']
                raise ValueError
            work_dict = {}
            work_dict['filename'] = filename
            for name, value in p.items(orig_section):
                name = name.lower()
                if name not in valid_values:
                    print "Found unsupported value, ignoring: %s %s" % (name, filename)
                    continue
                work_type = type(valid_values[name])
                if work_type == type([]):
                    value = value.split()
                elif work_type == type(''):
                    pass
                else:
                    print "Error: Unsupported type specified in valid_values"
                    print "Type was: %s" % work_type
                    raise ValueError
                work_dict[name] = value
            self.fsets[section] = FsetInstance(section, work_dict)

    def __getitem__(self, key):
        return self.fsets[key.lower()]

    def __str__(self):
        return ('<data="%s">'
                % (self.fsets))

class FsetInstance(object):
    def __init__(self, name, data_dict):
        self.name = name.lower()
        self.data = data_dict
    def __getitem__(self, key):
        return self.data[key.lower()]
    def __getattr__(self, name):
        return self.data[name.lower()]
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
