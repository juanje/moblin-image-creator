#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import os, commands, sys

if len(sys.argv) >= 2 and sys.argv[1] != "--test" :
    print "Usage: %s [--test]" % sys.argv[0]
    sys.exit(0)

TEST_RUN = ""
if len(sys.argv) > 1 and sys.argv[1] == "--test" :
    TEST_RUN = "--test"

LIST_FILE = "/etc/base-rpms.list"
list_file = open(LIST_FILE, 'r')

o_list = []
for i in list_file :
    rpm_name = i.rstrip()
    o_list.append(rpm_name)

COMMAND = "rpm -qa"
output = commands.getoutput(COMMAND)
n_list = output.splitlines()

for i in o_list :
    n_index = range(len(n_list))
    for j in n_index :
        if i == n_list[j] :
            del n_list[j]
            break

if not len(n_list) :
    print "no rpms to remove"
    sys.exit(0)

print "removing the following rpms: "
remove_list = ""
for i in n_list :
    print "\t %s " % i 
    remove_list += "%s " % i

REMOVE_CMD = "rpm -e --noscripts %s %s" % (TEST_RUN, remove_list)
os.system(REMOVE_CMD)


