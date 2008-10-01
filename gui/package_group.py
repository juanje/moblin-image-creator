#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

#    Copyright (c) 2008 Intel Corporation
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

import gettext
import gnome
import gobject
import gtk
import gtk.glade
import locale
import os
import pygtk
import re
import sys
import time
import traceback

import pdk_utils
import SDK

_ = gettext.lgettext


class packageGroup(object):
    def __init__(self, sdk, target):
        self.sdk = sdk
        self.target = target
        self.cmdOutput = []
        self.gladefile = os.path.join(self.sdk.path, "image-creator.glade")


    def run(self):
        self.target.chroot("yum grouplist", self.cmdOutput)
        installedGroups = False
        availableGroups = False
        done = False
        self.installedGroupList = []
        self.availableGroupList = []        
        
        for item in self.cmdOutput:
            if item == 'Installed Groups:':
                installedGroups = True
                continue
            if item == 'Available Groups:':
                availableGroups = True
                continue
            if item == 'Done':
                done = True            
                continue

            if installedGroups:
                if not availableGroups:
                    self.installedGroupList.append(item.strip())
            if availableGroups:
                if not done:
                    self.availableGroupList.append(item.strip())

        if not self.installedGroupList and not self.availableGroupList:
            self.show_error_dialog(_("Could not get Group List"))
        else:        
            #print "Installed Group: %s" % self.installedGroupList
            #print "Available Group: %s" % self.availableGroupList
            #print "Installing the following: %s" % self.setup_fsets_dialog()
            return self.setup_fsets_dialog()
          

    def setup_fsets_dialog(self, showFsets = ""):
        tree = gtk.glade.XML(self.gladefile, 'fsetsDialog')
        dialog = tree.get_widget('fsetsDialog')
        dialog.set_title("Install Package Groups")
        vbox = tree.get_widget('vbox')
        debugVbox = tree.get_widget('vbox8')

        groupsToInstall = []
    
        list = gtk.ListStore(gobject.TYPE_STRING)
        iter = 0
        #groupTouple is a list of touples
        #Each touple has 2 elements - group name, gtk.CheckButton

        self.groupTouple = [("", gtk.CheckButton(""))]

        for group_name in sorted(self.availableGroupList):
            iter = list.append([group_name])
            buttonName = group_name # + "  (" + platform.fset[fset_name].desc + ")"
            self.groupTouple.append((group_name, gtk.CheckButton(buttonName)))
            #toolTipText = _("<b>Depends on FSet(s):</b> ")
            #for depends in sorted(platform.fset[fset_name].deps):
            #    toolTipText += " %s " % depends
            #toolTipText += _("\n<b>Debug Packages:</b> ")
            #for debug_pkgs in sorted(platform.fset[fset_name].debug_pkgs):
            #    toolTipText += " %s " % debug_pkgs
            #toolTipText += _("\n<b>Packages:</b> ")
            #for pkgs in sorted(platform.fset[fset_name].pkgs):
            #    toolTipText += " %s " % pkgs
            #if self.pygtkOldVersion == False:
            #    self.fsetTouple[i][1].set_tooltip_markup(toolTipText)          

        if not iter:
            self.show_error_dialog(_("Nothing available to install!"))
            dialog.destroy()
            return

        self.groupTouple.pop(0)
        for checkBox in self.groupTouple:
            vbox.pack_start(checkBox[1])

        for group_name in sorted(self.installedGroupList):
            buttonName = group_name + _(" is already installed")# + "  (" + platform.fset[fset_name].desc + ")"            
            checkBox = gtk.CheckButton(buttonName)
            checkBox.set_sensitive(False)
            checkBox.set_active(True)
            vbox.pack_start(checkBox)

        dialog.show_all()
        #Hide the debug check box
        debugVbox.hide_all()

        while True:
            if dialog.run() == gtk.RESPONSE_OK:
                numGroupsToInstall = 0
                for checkBox in self.groupTouple:
                    if checkBox[1].get_active():
                        groupsToInstall.append(checkBox[0])
                    
                print _("Number of groups to install: %s") % numGroupsToInstall

                if groupsToInstall:
                    dialog.destroy()
                    break
                else:
                    print _("No Groups selected")
                    self.show_error_dialog(_("Please Choose a Group"))
            else:
                break
        dialog.destroy()
        return groupsToInstall                   


    def show_error_dialog(self, message= _("An unknown error has occurred!")):
        widgets = gtk.glade.XML(self.gladefile, 'error_dialog')
        widgets.get_widget('error_label').set_text(message)
        dialog = widgets.get_widget('error_dialog')
        dialog.run()
        dialog.destroy()

if __name__ == '__main__':
    sys.exit(main())

