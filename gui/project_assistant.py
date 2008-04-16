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
import mic_cfg

class projectConfiguration(object):
    def __init__(self, projectName, projectDesc, projectPath, projectPlatform, targetName, fsetsToInstall, debugPkgs):
        self.projectName = projectName
        self.projectDesc = projectDesc
        self.projectPath = projectPath
        self.projectPlatform = projectPlatform
        self.targetName = targetName
        self.fsetsToInstall = fsetsToInstall
        self.debugPkgs = debugPkgs

class projectAssistant(object):
    """Class to create the Project Creation Assistant"""
    def __init__(self, sdk):
        """Function will initiate the necessary GUI elements for Project Assistant"""

        # Need PyGTK >= 2.12.0 for our tooltips
        if gtk.pygtk_version >= (2,12,0):
            self.pygtkOldVersion = False
        else:
            self.pygtkOldVersion = True

        self.projectName = ""
        self.projectDesc = ""
        self.projectPath = ""
        self.projectPlatform = ""        
        self.targetName = ""
        self.debugPackageSelected = False
        self.fsetsToInstall = []
        self.newProjectconfig = projectConfiguration("", "", "", "", "", [], "")

        self.quitting = False
        self.sdk = sdk

        self.checkBoxContainer = None
        sideImage = gtk.gdk.pixbuf_new_from_file("/usr/share/pdk/mic-assistant.xpm")
        headImage = gtk.gdk.pixbuf_new_from_file("/usr/share/pdk/image-creator-32x32.xpm")
        
        #Setting up the Assistant Widget
        self.assistantDialog = gtk.Assistant()        
        self.assistantDialog.set_size_request(800, 500)
        self.assistantDialog.connect("close", self.quit)
        self.assistantDialog.connect("cancel", self.quit)
        self.assistantDialog.connect("apply", self.apply)
        self.assistantDialog.connect("prepare", self.prepare)

       
        #Setting up the Introduction Page of the Assistant
        introductionPage = gtk.HBox()
        self.assistantDialog.append_page(introductionPage)
        self.assistantDialog.set_page_title(introductionPage, "Introduction")
        self.assistantDialog.set_page_type(introductionPage, gtk.ASSISTANT_PAGE_INTRO)
        self.assistantDialog.set_page_complete(introductionPage, True)
        self.assistantDialog.set_page_side_image(introductionPage, sideImage)
        self.assistantDialog.set_page_header_image(introductionPage, headImage)

        introductionLabel = gtk.Label()
        introductionLabel.set_markup("<b>This assistant will help you to create a project and a target.\nYou also will be able to select which functional sets (fsets) to install.</b>")      
        introductionPage.pack_end(introductionLabel)

        #Setting up the Project Creation Page of the Assistant
        self.projectPage = gtk.HBox()
        self.assistantDialog.append_page(self.projectPage)
        self.assistantDialog.set_page_title(self.projectPage, "Create Project")
        self.assistantDialog.set_page_type(self.projectPage, gtk.ASSISTANT_PAGE_CONTENT)
        self.assistantDialog.set_page_complete(self.projectPage, False)
        self.assistantDialog.set_page_side_image(self.projectPage, sideImage)
        self.assistantDialog.set_page_header_image(self.projectPage, headImage)

        projectPageVbox = self.create_project_page()
        self.projectPage.pack_end(projectPageVbox)
      

        #Setting up the Target and FSets Page of the Assistant
        self.targetPage = gtk.HBox()
        self.assistantDialog.append_page(self.targetPage)
        self.assistantDialog.set_page_title(self.targetPage, "Create Target and add Fsets")
        self.assistantDialog.set_page_type(self.targetPage, gtk.ASSISTANT_PAGE_CONTENT)
        self.assistantDialog.set_page_complete(self.targetPage, False)
        self.assistantDialog.set_page_side_image(self.targetPage, sideImage)
        self.assistantDialog.set_page_header_image(self.targetPage, headImage)

        targetPageVbox = self.create_target_page()
        self.targetPage.pack_end(targetPageVbox)


        #Setting up the Confirmation Page of the Assistant
        self.confirmPage = gtk.HBox()
        self.assistantDialog.append_page(self.confirmPage)
        self.assistantDialog.set_page_title(self.confirmPage, "Confirm")
        self.assistantDialog.set_page_type(self.confirmPage, gtk.ASSISTANT_PAGE_CONFIRM)
        self.assistantDialog.set_page_complete(self.confirmPage, True)
        self.assistantDialog.set_page_side_image(self.confirmPage, sideImage)
        self.assistantDialog.set_page_header_image(self.confirmPage, headImage)


        confirmLabel = gtk.Label("Please review the configuration before proceeding.")
        self.confirmConfigurationVbox = gtk.VBox()

        self.confirmPageNameLable = gtk.Label("")
        self.confirmConfigurationVbox.pack_start(self.confirmPageNameLable)
        self.confirmPageDescLabel = gtk.Label("")
        self.confirmConfigurationVbox.pack_start(self.confirmPageDescLabel)
        self.confirmPagePathLabel = gtk.Label("")
        self.confirmConfigurationVbox.pack_start(self.confirmPagePathLabel)
        self.confirmPagePlatformLabel = gtk.Label("")
        self.confirmConfigurationVbox.pack_start(self.confirmPagePlatformLabel)
        self.confirmPageTargetLabel = gtk.Label("")
        self.confirmConfigurationVbox.pack_start(self.confirmPageTargetLabel)        
        self.confirmPageFsetListLabel = gtk.Label("")
        self.confirmConfigurationVbox.pack_start(self.confirmPageFsetListLabel)
        self.confirmPageDebugLabel = gtk.Label("")
        self.confirmConfigurationVbox.pack_start(self.confirmPageDebugLabel)

        self.confirmConfigurationVbox.pack_start(confirmLabel)
        self.confirmPage.pack_end(self.confirmConfigurationVbox)


        self.assistantDialog.show_all()

    def quit(self, widget, event = None):
        """Kill the Assistant Dialog upon quit signal"""
        self.quitting = True

    def apply(self, widget, event = None):
        """This function will be called when the Apply button in the final page is clicked
        Note: The dialog should not be destroyed here"""
        self.newProjectconfig = projectConfiguration(self.projectName, self.projectDesc, self.projectPath, self.projectPlatform, self.targetName, self.fsetsToInstall, self.debugPackageSelected)
        

    def prepare(self, widget, page):
        if page == self.targetPage:
            platformName = self.projectPlatformCombo.get_active_text().split()[0]  
            self.setup_fset_check_box(platformName)
        if page == self.confirmPage:
            self.projectName = self.projectNameEntry.get_text()
            self.projectDesc = self.projectDescEntry.get_text()
            self.projectPath = self.projectPathEntry.get_text()
            self.projectPlatform = self.projectPlatformCombo.get_active_text().split()[0]
        
            self.targetName = self.targetNameEntry.get_text()
            self.debugPackageSelected = self.targetDebugPkgs.get_active()

            self.fsetsToInstall = []
            for fsetName in self.fsetTouple:
                if fsetName[2] == True:
                    self.fsetsToInstall.append(fsetName[0])

            self.display_configuration()         
          

    def create_project_page(self):
        """Creates the necessary GUI elements for the project page of the Assistant"""
        projectNameLabel = gtk.Label("Project Name")
        self.projectNameEntry = gtk.Entry()

        projectDescLabel = gtk.Label("Project Description")
        self.projectDescEntry = gtk.Entry()

        projectPathLabel = gtk.Label("Project Path")
        self.projectPathEntry = gtk.Entry()
        path = os.getcwd() + os.sep
        self.projectPathEntry.set_text(path)
        projectPathBrowse = gtk.Button("Browse")
        projectPath = gtk.HBox()
        projectPath.pack_start(self.projectPathEntry, True, True, 0)        
        projectPath.pack_start(projectPathBrowse, False, False, 0)
      
        projectPathBrowse.connect("clicked", self.fill_project_path)
        self.projectNameEntry.connect("changed", self.project_entry_callback)
        self.projectDescEntry.connect("changed", self.project_entry_callback)
        self.projectPathEntry.connect("changed", self.project_entry_callback)

        projectPlatformLabel = gtk.Label("Project Platform")
        projectPlatformDescLabel = gtk.Label("Platform Description")
        self.projectPlatformDesc = gtk.TextBuffer()
        projectPlatformDescText = gtk.TextView(self.projectPlatformDesc)
        projectPlatformDescText.set_wrap_mode(gtk.WRAP_WORD)
        projectPlatformDescText.set_editable(False)
        
        
        #projectPlatformCombo = gtk.ComboBox()
        #Easier way to build a combo box with text only
        self.projectPlatformCombo = gtk.combo_box_new_text()

        #populate the combo box with available platforms
        platformList = sorted(self.sdk.platforms.iterkeys())
        platform_idx = 0
        packageManager = ""
        platform = ""

        if mic_cfg.config.has_option('general', 'package_manager'):
            packageManager = mic_cfg.config.get('general', 'package_manager')

        idx = 0
        for pname in platformList:
            pdesc = ""
            packageManagerDesc = ""
            added = False
            if self.sdk.platforms[pname].config_info != None:
                pdesc = " - (%s)" % self.sdk.platforms[pname].config_info['description']
                packageManagerDesc = self.sdk.platforms[pname].config_info['package_manager']
            if packageManager == packageManagerDesc:
                self.projectPlatformCombo.append_text(pname)
                added = True
            elif packageManagerDesc == "":
                self.projectPlatformCombo.append_text(pname)
                added = True
            # If previously selected an entry, select it again
            if added:
                if  (pname + pdesc) == platform:
                    platform_idx = idx
                idx += 1

        #projectPlatformCombo.set_model(platformComboList)
        self.projectPlatformCombo.connect("changed", self.project_platform_callback)
        self.projectPlatformCombo.set_active(platform_idx)

       
        self.projectWarning = gtk.Label()

        #projectPageVbox = gtk.VBox()
        #projectPageVbox.pack_start(projectName)
        #projectPageVbox.pack_start(projectDesc)
        #projectPageVbox.pack_start(projectPath)
        #projectPageVbox.pack_start(projectPlatform)
        #projectPageVbox.pack_start(self.projectWarning)

        projectPageTable = gtk.Table(5, 3, True)
        projectPageTable.set_homogeneous(False)
        projectPageTable.attach(projectNameLabel, 0, 1, 0, 1, 0, 0, 0, 5)
        projectPageTable.attach(self.projectNameEntry, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, 0, 0, 5)
        projectPageTable.attach(projectDescLabel, 0, 1, 1, 2, 0, 0, 0, 5)
        projectPageTable.attach(self.projectDescEntry, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, 0, 0, 5)
        projectPageTable.attach(projectPathLabel, 0, 1, 2, 3, 0, 0, 0, 5)
        projectPageTable.attach(projectPath, 1, 2, 2, 3, gtk.EXPAND|gtk.FILL, 0, 0, 5)
        projectPageTable.attach(projectPlatformLabel, 0, 1, 3, 4, 0, 0, 0, 5)
        projectPageTable.attach(self.projectPlatformCombo, 1, 2, 3, 4, gtk.EXPAND|gtk.FILL, 0, 0, 5)
        projectPageTable.attach(projectPlatformDescLabel, 0, 1, 4, 5, 0, 0, 0, 5)
        projectPageTable.attach(projectPlatformDescText, 1, 2, 4, 5, gtk.EXPAND|gtk.FILL, 0, 0, 5)

        projectPageVbox = gtk.VBox()
        projectPageVbox.pack_start(projectPageTable)
        projectPageVbox.pack_start(self.projectWarning)

        return projectPageVbox

    def fill_project_path(self, widget):
        """This function open a File Chooser Dialog which automatically fills in the Path Text Entry field in the Project Page"""
        dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, title="Choose Project Directory")
        dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        if dialog.run() == gtk.RESPONSE_OK:
            self.projectPathEntry.set_text(dialog.get_current_folder())
        dialog.destroy()

    def project_platform_callback(self, widget):
        pname = self.projectPlatformCombo.get_active_text()        
        self.projectPlatformDesc.set_text(self.sdk.platforms[pname].config_info['description'])
        

    def project_entry_callback(self, widget):
        """When the text entries in the Project page change, we need to validate the input before proceeding to the next page.
        Need to check if the project path is an empty or new directory and none of the fields are blank"""
        if not self.projectNameEntry.get_text() or not self.projectDescEntry.get_text() or not self.projectPathEntry.get_text():
            self.assistantDialog.set_page_complete(self.projectPage, False)
        else:
            if not os.path.exists(self.projectPathEntry.get_text()):
                self.assistantDialog.set_page_complete(self.projectPage, True)
                self.projectWarning.set_text("")
            else:
                if not os.path.isdir(self.projectPathEntry.get_text()):
                    self.projectWarning.set_text("Path exists but is not a directory")                
                    self.assistantDialog.set_page_complete(self.projectPage, False)
                else:
                    # Make sure that the directory specified is empty    
                    if len(os.listdir(self.projectPathEntry.get_text())):
                        self.projectWarning.set_text("Path is a directory which is NOT empty")
                        self.assistantDialog.set_page_complete(self.projectPage, False)
            
    def create_target_page(self):
        """Creates the GUI elements for target page of the assistant"""
        targetNameLabel = gtk.Label("Target Name")
        self.targetNameEntry = gtk.Entry()
        targetNameHbox = gtk.HBox()
        targetNameHbox.pack_start(targetNameLabel, False, False, 10)
        targetNameHbox.pack_start(self.targetNameEntry, True, True, 10)

        self.targetWarning = gtk.Label()

        targetName = gtk.VBox()
        targetName.pack_start(targetNameHbox, False, False, 10)
        targetName.pack_start(self.targetWarning, False, False, 10)



        self.targetNameEntry.connect("changed", self.target_entry_callback)

        self.targetFsetVbox = gtk.VBox()
            
        self.targetDebugPkgs = gtk.CheckButton("Include Debug packages (if any)")        
        targetPageSeparator1 = gtk.HSeparator()
        targetPageSeparator2 = gtk.HSeparator()
        
        targetPageVbox = gtk.VBox()
        targetPageVbox.pack_start(targetName)
        targetPageVbox.pack_start(targetPageSeparator1)
        targetPageVbox.pack_start(self.targetFsetVbox)
        targetPageVbox.pack_start(targetPageSeparator2)
        targetPageVbox.pack_start(self.targetDebugPkgs)


        return targetPageVbox

    def setup_fset_check_box(self, platformName):
        """Move setting up fset check boxes to a different function since it can be setup only after the platform is selected""" 
        if self.checkBoxContainer != None:
            self.targetFsetVbox.remove(self.checkBoxContainer)
        self.checkBoxContainer = gtk.VBox()
        targetFsetLabel = gtk.Label()
        targetFsetLabel.set_markup("<b>Available Fsets for the choosen platform</b>")
        self.checkBoxContainer.pack_start(targetFsetLabel)        
        
        platform = self.sdk.platforms[platformName]
        self.currentPlatformSelected = platform
        all_fsets = set(platform.fset)
        installed_fsets = set()
        list = gtk.ListStore(gobject.TYPE_STRING)
        iter = 0
        #fsetTouple is a list of touples
        #Each touple has 4 elements - fset name, gtk.CheckButton, bool (indicating if that fset needs to be installed) and int (number of fsets that depend on it)
        self.fsetTouple = [("", gtk.CheckButton(""), False, 0)]
        i = 1
        for fset_name in sorted(all_fsets.difference(installed_fsets)):
            iter = list.append([fset_name])
            buttonName = fset_name + "  (" + platform.fset[fset_name].desc + ")"
            self.fsetTouple.append((fset_name, gtk.CheckButton(buttonName), False, 0))       
            toolTipText = "<b>Depends on FSet(s):</b> "
            for depends in sorted(platform.fset[fset_name].deps):
                toolTipText += " %s " % depends
            toolTipText += "\n<b>Debug Packages:</b> "
            for debug_pkgs in sorted(platform.fset[fset_name].debug_pkgs):
                toolTipText += " %s " % debug_pkgs
            toolTipText += "\n<b>Packages:</b> "
            for pkgs in sorted(platform.fset[fset_name].pkgs):
                toolTipText += " %s " % pkgs
            if self.pygtkOldVersion == False:
                self.fsetTouple[i][1].set_tooltip_markup(toolTipText)
            i += 1
        self.fsetTouple.pop(0)

        i = 0
        for checkBox in self.fsetTouple:
            checkBox[1].connect("clicked", self.checkBoxCallback, checkBox[0])
            self.checkBoxContainer.pack_start(checkBox[1])

        self.targetFsetVbox.pack_start(self.checkBoxContainer)
        self.assistantDialog.show_all()

    def checkBoxCallback(self, widget, fSetName):
        """Call back function when the check box is clicked. This function calculates all dependencies of fsets and checks the rest of the boxes"""
        #platform = self.current_project().platform
        platform = self.currentPlatformSelected
        fset = platform.fset[fSetName]
        active = False
        for i, item in enumerate(self.fsetTouple):
            if fSetName == item[0]:
                active = self.fsetTouple[i][1].get_active()
                self.fsetTouple[i] = (self.fsetTouple[i][0], self.fsetTouple[i][1], True, self.fsetTouple[i][3])
        if active == True:
            i = 0
            for item in self.fsetTouple:
                if fSetName != item[0]:
                    for dep in fset['deps']:
                        if dep == item[0]:
                            if self.fsetTouple[i][1].get_active() == False:
                                self.fsetTouple[i][1].set_active(True)
                                #sex_active causes this function to be called recurssively
                            self.fsetTouple[i][1].set_sensitive(False)
                            self.fsetTouple[i] = (self.fsetTouple[i][0], self.fsetTouple[i][1], False, self.fsetTouple[i][3] + 1)
                i = i + 1
        else:
            i = 0
            for item in self.fsetTouple:
                if fSetName != item[0]:
                    for dep in fset['deps']:
                        if dep == item[0]:
                            self.fsetTouple[i] = (self.fsetTouple[i][0], self.fsetTouple[i][1], False, self.fsetTouple[i][3] - 1)
                            if self.fsetTouple[i][3] == 0:
                                if self.fsetTouple[i][1].get_active() == True:
                                    self.fsetTouple[i][1].set_active(False)
                                self.fsetTouple[i][1].set_sensitive(True)
                else:
                    self.fsetTouple[i] = (self.fsetTouple[i][0], self.fsetTouple[i][1], False, self.fsetTouple[i][3])
                i = i + 1




    def target_entry_callback(self, widget):
        """Function to validate all the inpus of the target page before moving to the next page"""
        if not self.targetNameEntry.get_text():
            self.assistantDialog.set_page_complete(self.targetPage, False)
        else:
            if re.search(r'[^-_a-zA-Z0-9]', self.targetNameEntry.get_text()):
                self.targetWarning.set_text("Target names can only contain alpha/numeric characters, hyphen and underscore")
                self.assistantDialog.set_page_complete(self.targetPage, False)
            else:
                self.targetWarning.set_text("")
                self.assistantDialog.set_page_complete(self.targetPage, True)
            

    def display_configuration(self):
            self.confirmPageNameLable.set_text("Project Name: %s" % self.projectName)
            self.confirmPageDescLabel.set_text("Project Description: %s" % self.projectDesc)
            self.confirmPagePathLabel.set_text("Project Path: %s" % self.projectPath)
            self.confirmPagePlatformLabel.set_text("Project Platform: %s" % self.projectPlatform)
            self.confirmPageTargetLabel.set_text("Target Name: %s" % self.targetName)
            self.confirmPageFsetListLabel.set_text("Fset List: %s" % self.fsetsToInstall)
            self.confirmPageDebugLabel.set_text("Install Debug Packages: %s" % self.debugPackageSelected)         
            #self.assistantDialog.show_all()


    def run(self):
        """This function will simiulate the Assistant as a dialog to the caller. This is required since the gtk.Assistant is not derived from gtk.Dialog.
        Thus the run() function is not available in the Assistant"""

        while self.quitting == False:
            gtk.main_iteration(False)
        self.assistantDialog.destroy()

        return self.newProjectconfig

if __name__ == '__main__':
    sys.exit(main())
