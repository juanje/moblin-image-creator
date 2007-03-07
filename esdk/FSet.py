#!/usr/bin/python

import os, re, sys

class FSet:
	"""
        An FSet object represents a functional set of packages to install in a
        target filesystem.  An FSet contains an array of package names in
        FSet.packages, an array of additional debug packages in
        FSet.debug_packages, and an array of dependant FSet names in FSet.deps.
	"""
	def __init__(self, path):
		self.path = os.path.abspath(os.path.expanduser(path))
		self.name = ''
		self.packages = []
		self.debug_packages = []
		self.deps = []
		self.desc = ''

		# Parse the fset file
                string_vals = ['name', 'desc']
                list_vals = {'pkgs' : 'packages', 'debug_pkgs' : 'debug_packages', 'deps' : 0}
		fset = open(self.path)
                for line in fset:
                        if re.search(r'^\s*#', line):
                            continue
                        try:
                            key, value = line.split('=')
                        except:
                            continue
                        key = key.lower().strip()
                        value = value.strip()
                        if key in string_vals:
                            exec('self.%s = value' % key)
                            continue
                        if key in list_vals:
                            # See if we want to store the value under a
                            # different identifier
                            if list_vals[key]:
                                new_key = list_vals[key]
                            else:
                                new_key = key
                            exec('self.%s = value.split()' % new_key)
                            continue
		fset.close()
                self.debug_packages.sort()
                self.deps.sort()
                self.packages.sort()

	def __str__(self):
		return ('<name="%s", desc="%s", packages=%s, debug_packages=%s, deps=%s>' 
                        % (self.name, self.desc, self.packages, self.debug_packages, self.deps))

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print >> sys.stderr, "USAGE: %s FSET_FILE ..." % (sys.argv[0])
	else:
		for file in sys.argv[1:]:
			print FSet(file);
