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

import gettext
import gnome
import gobject
import gtk
import os
import pygtk
import re
import shutil
import sys
import time
import traceback
import signal
import Platform
from threading import Thread

import pdk_utils
import SDK
import mic_cfg
import project_assistant
import repo_editor
import package_group
import paths

debug = False
if mic_cfg.config.has_option('general', 'debug'):
    debug = int(mic_cfg.config.get('general', 'debug'))

_ = gettext.lgettext
    
mountedDirs = set()
class term_mic(Thread):
    def __init__(self, sdk, micApp):
        Thread.__init__(self)
        self.sdk = sdk
        self.app = micApp
    
    def run(self):
        print _("Unmounting all mounted directories...")
        global mountedDirs
        directory_set = self.sdk.umount()
        if directory_set:
            print _("Could not unmount these dirs: %s") % directory_set
            mountedDirs = directory_set.copy()
        print _("Unmounting complete")


class App(object):
    """This is our main"""
    def __init__(self):
        # Need PyGTK >= 2.12.0 for our tooltips
        if gtk.pygtk_version >= (2,12,0):
            self.pygtkOldVersion = False
        else:
            self.pygtkOldVersion = True

        self.sdk = SDK.SDK(progress_callback = self.gui_throbber, status_label_callback = self.set_status_label)
        self.gladefile = os.path.join(self.sdk.path, "image-creator.glade")
        if not os.path.isfile(self.gladefile):
            raise IOError, "Glade file is missing from: %s" % self.gladefile
        gnome.init('image-creator', self.sdk.version, properties = {'app-datadir':self.sdk.path})
        self.widgets = gtk.glade.XML (self.gladefile, 'main')
        dic = {"on_main_destroy_event" : self.quit,
                "on_quit_activate" : self.quit,
                "on_help_activate" : self.on_help_activate,
                "on_new_project_clicked" : self.on_new_project_clicked,
                "on_projectDelete_clicked": self.on_projectDelete_clicked,
                "on_new_target_add_clicked": self.on_new_target_add_clicked,
                "on_delete_target_clicked": self.on_delete_target_clicked,
                "on_install_fset": self.on_install_fset,
                "on_install_group": self.on_install_group,
                "on_create_liveUSB_clicked": self.on_liveUSB_clicked,
                "on_create_liveRWUSB_clicked": self.on_liveRWUSB_clicked,
                "on_create_NFSliveUSB_clicked": self.on_NFSliveUSB_clicked,
                "on_create_installUSB_clicked": self.on_installUSB_clicked,
                "on_create_liveCD_clicked": self.on_liveCD_clicked,
                "on_create_NFSliveCD_clicked": self.on_NFSliveCD_clicked,
                "on_create_installCD_clicked": self.on_installCD_clicked,
                "on_create_NAND_btn_clicked": self.on_NAND_clicked,
                "on_about_activate": self.on_about_activate,
                "on_term_launch_clicked": self.on_term_launch_clicked,
                "on_target_term_launch_clicked": self.on_target_term_launch_clicked,
                "on_target_config_clicked": self.on_target_config_clicked,
                "on_Write_USB_clicked": self.writeUsbImage,
                "on_launch_vm_btn_clicked": self.on_launch_vm_clicked, 
                "on_WriteUsbImage_activate":self.on_WriteUsbImage_activate,
                "on_ClearRootstraps_activate":self.on_ClearRootstraps_activate,
                "on_Load_activate":self.on_Load_activate,
                "on_Save_activate":self.on_Save_activate,
                "on_upgrade_project_clicked":self.on_upgrade_project_clicked,
                "on_upgrade_target_clicked":self.on_upgrade_target_clicked,
                "on_editRepo_clicked":self.on_editRepo_clicked,
                "on_MirrorSettings_activate":self.on_MirrorSettings_activate,
                "on_Add_Project_Wizard_activate":self.on_Add_Project_Wizard_activate,
                "on_fsetsInfo_activate":self.on_fsetsInfo_activate,
                "on_editRepo_activate": self.on_editRepo_activate,
                "on_cmd_history_clicked": self.on_cmd_history_clicked
                }
        self.widgets.signal_autoconnect(dic)
        # setup projectView widget
        self.pName = _("Name")
        self.pDesc = _("Description")
        self.pPath = _("Path")
        self.pPlatform = _("Platform")
        self.projectView = self.widgets.get_widget("projectView")
        self.set_plist(self.pName, 0)
        self.set_plist(self.pDesc, 1)
        self.set_plist(self.pPath, 2)
        self.set_plist(self.pPlatform, 3)
        self.projectList = gtk.ListStore(str, str, str, str)
        # Set targetView widget
        self.tName = _("Name")
        self.tFSet = _("Function Sets")
        self.tUpdates = _("Updates")
        self.targetView = self.widgets.get_widget("targetView")
        self.set_tlist(self.tName, 0)
        self.set_tlist(self.tFSet, 1)
        self.set_tlist(self.tUpdates, 2)
        self.targetList = gtk.ListStore(str, str, str)
        self.targetView.set_model(self.targetList)
        self.buttons = MainWindowButtons(self.widgets)
        # read in project list using SDK()
        self.refreshProjectList()
        # Connect project selection signal to list targets in the targetList
        # widget: targetView
        self.projectView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.targetView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.projectView_handler = self.projectView.get_selection().connect("changed", self.project_view_changed)
        self.targetView_handler = self.targetView.get_selection().connect("changed", self.target_view_changed)

        main_window = self.widgets.get_widget("main")
        main_window.set_resizable(True)
        #main_window.set_size_request(900, 600)

        self.newFeatureDialog()        
        obsolete_projects = self.sdk.return_obsolete_projects()
        if obsolete_projects:         
            error_message = ""
            for proj in obsolete_projects:
                error_message = error_message + " " + proj
            self.show_error_dialog(_("Found unsupported project(s): %s\nskipping them") % error_message)

        self.cmd_history=[]

    def run(self):
        gtk.main()

    def quit(self, value):
        # Unmount all of our projects
        global mountedDirs
        mountedDirs = set()
        term_thread = term_mic(self.sdk, self)
        term_thread.start()

        widgets = gtk.glade.XML(self.gladefile, 'error_dialog')
        widgets.get_widget('error_label').set_text(_("Please wait while MIC attempts to unmount all projects and targets..."))
        dialog = widgets.get_widget('error_dialog')
        vbox = widgets.get_widget('vbox18')
        progressbar = gtk.ProgressBar()
        vbox.pack_start(progressbar)
        dialog.connect('delete_event', self.ignore)
        dialog.set_title(_("Closing Image-Creator"))
        ok_button = widgets.get_widget('okbutton4')
        ok_button.set_sensitive(False)
        dialog.show_all()   
        while term_thread.isAlive():
            while gtk.events_pending():
                gtk.main_iteration(False)
            time.sleep(0.20)
            progressbar.pulse()
        dialog.destroy()
        if mountedDirs:
            self.show_umount_error_dialog(mountedDirs)
        gtk.main_quit()

    def on_help_activate(self, widget):
        gnome.help_display('image-creator')

    def newFeatureDialog(self):
        if self.pygtkOldVersion == True:
            self.show_error_dialog(_("You are using an old version of PyGTK. Image Creator required atleast PyGTK 2.12. Some features will be disabled"))
            return
        if os.path.isfile(paths.PKGDATADIR + "/newFeature"):
            newFeatureTree = gtk.glade.XML(self.gladefile, 'newFeature')
            newFeatureDialog = newFeatureTree.get_widget('newFeature')
            newFeatureLabel = newFeatureTree.get_widget('newFeatureLabel')
            newFeatureText = ""
            f = open(paths.PKGDATADIR + "/newFeature")
            for line in f:
                newFeatureText += "\n"
                newFeatureText += line
            newFeatureLabel.set_text(newFeatureText)
            newFeatureDialog.set_size_request(400, 250)
            newFeatureDialog.run()
            newFeatureDialog.destroy()
            os.unlink(paths.PKGDATADIR + "/newFeature")

    def target_view_changed(self, selection):
        num_rows_selected = self.targetView.get_selection().count_selected_rows()
        target_selected_state = False
        delete_target_state = False
        fset_state = False
        if num_rows_selected == 0:
            pass
        elif num_rows_selected == 1:
            # A target is selected
            target_selected_state = True
            delete_target_state = True
            target = self.current_target()
            fsets = target.installed_fsets()
            if fsets:
                # We have fsets installed in the target
                fset_state = True
        else:
            delete_target_state = True
        # Items which should be enabled if we have a target selected
        self.buttons.delete_target.set_sensitive(delete_target_state)
        self.buttons.install_fset.set_sensitive(target_selected_state)
        self.buttons.target_term_launch.set_sensitive(target_selected_state)
        self.buttons.upgrade_target.set_sensitive(target_selected_state)
        self.buttons.edit_repo.set_sensitive(target_selected_state)
        self.buttons.install_group.set_sensitive(target_selected_state)
        # Items which should be enabled if our selected target has an fset
        self.buttons.create_liveusb.set_sensitive(fset_state)
        self.buttons.create_liverwusb.set_sensitive(fset_state)
        self.buttons.create_nfsliveusb.set_sensitive(fset_state)
        self.buttons.create_installusb.set_sensitive(fset_state)
        self.buttons.target_config.set_sensitive(fset_state)
        self.buttons.create_liveCD.set_sensitive(fset_state)
        self.buttons.create_nfsliveCD.set_sensitive(fset_state)
        self.buttons.create_installCD.set_sensitive(fset_state)
        self.buttons.create_NAND.set_sensitive(fset_state)
        self.buttons.Write_USB.set_sensitive(fset_state)
        self.buttons.create_launchvm.set_sensitive(fset_state)

    def project_view_changed(self, selection):
        num_rows_selected = self.projectView.get_selection().count_selected_rows()
        if num_rows_selected == 1:
            try:
                self.current_project().mount()
            except:
                pass
        self.redraw_target_view()

    def redraw_target_view(self):
        self.targetList.clear()
        num_rows_selected = self.projectView.get_selection().count_selected_rows()
        if num_rows_selected == 0:
            # No projects are selected. Disable all buttons
            self.buttons.delete_project.set_sensitive(False)
            self.buttons.upgrade_project.set_sensitive(False)
            self.buttons.add_target.set_sensitive(False)
            self.buttons.install_fset.set_sensitive(False)
            self.buttons.install_group.set_sensitive(False)   
            self.buttons.delete_target.set_sensitive(False)
            self.buttons.term_launch.set_sensitive(False)
            return
        if num_rows_selected > 1:
            #Multiple projects are selected. Only the 'delete project' button should be active
            self.buttons.delete_project.set_sensitive(True)
            self.buttons.upgrade_project.set_sensitive(False)
            self.buttons.add_target.set_sensitive(False)
            self.buttons.install_fset.set_sensitive(False)
            self.buttons.install_group.set_sensitive(False)
            self.buttons.delete_target.set_sensitive(False)
            self.buttons.term_launch.set_sensitive(False)
            return
        # We have a project selected, so it makes sense for the delete project
        # and add target buttons to be sensitive
        self.buttons.delete_project.set_sensitive(True)
        self.buttons.add_target.set_sensitive(True)
        self.buttons.term_launch.set_sensitive(True)
        self.buttons.upgrade_project.set_sensitive(True)

        progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
        progress_dialog = progress_tree.get_widget('ProgressDialog')
        progress_dialog.set_size_request(450, 250)
        progress_dialog.connect('delete_event', self.ignore)
        progress_tree.get_widget('progress_label').set_text(_("Checking for updates..."))
        self.progressbar = progress_tree.get_widget('progressbar')
        self.statuslabel = progress_tree.get_widget('status_label')

        for key in sorted(self.current_project().targets):
            installed_fsets = ' '.join(self.current_project().targets[key].installed_fsets())
            if self.current_project().platform.config_info['package_manager'] == 'yum':
                cmdOutput = []
                retVal = self.current_project().targets[key].chroot("yum check-update", cmdOutput)
                if retVal == 100:
                    self.targetList.append((key, installed_fsets, "Updates availalbe for %s packages" % len(cmdOutput)))
                elif retVal == 0:
                        self.targetList.append((key, installed_fsets, "None"))
                else:
                    self.targetList.append((key, installed_fsets, "Could not retrieve information"))
            else:
                    self.targetList.append((key, installed_fsets, "Info Not Available"))
        if self.current_project().targets:
            selection = self.targetView.get_selection()
            selection.select_path(0)
        progress_dialog.destroy()

    def set_plist(self, name, id):
        """Add project list column descriptions"""
        column = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=id)
        column.set_resizable(True)
        column.set_sort_column_id(id)
        self.projectView.append_column(column)

    def set_tlist(self, name, id):
        """Add target list column descriptions"""
        column = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=id)
        column.set_resizable(True)
        column.set_sort_column_id(id)
        self.targetView.append_column(column)

    def stop_progress(self, widget, cancelData):        
        #self.stopTest = True
        tree = gtk.glade.XML(self.gladefile, 'qDialog')
        tree.get_widget('queryLabel').set_text(_("Are you sure you want to cancel project creation?"))
        tree.get_widget('cancelbutton2').set_label("gtk-no")
        tree.get_widget('okbutton2').set_label("gtk-yes")
        dialog = tree.get_widget('qDialog')
        result = dialog.run()
        dialog.destroy()       
        if result == gtk.RESPONSE_OK:
            cur_pid = os.getpid()
            child_list = pdk_utils.findChildren(cur_pid)
            for child in child_list:
                if child != cur_pid:
                    os.kill(child, signal.SIGKILL)
        print _("Canceled Function was %s and cancel type was %s") % (cancelData[0], cancelData[1])


    def on_new_project_clicked(self, widget):
        """Instantiate a new dialogue"""
        name = ""
        desc = ""
        platform = ""
        # Use current working directory as a starting point
        path = os.getcwd() + os.sep
        while True:
            dialog = AddNewProject(sdk = self.sdk, name = name, gladefile = self.gladefile, desc = desc, platform = platform, path = path)
            result = dialog.run()
            if result != gtk.RESPONSE_OK:
                break
            name = dialog.name
            desc = dialog.desc
            target_name = dialog.target_name
            platform = dialog.platform
            path = os.path.realpath(os.path.abspath(os.path.expanduser(dialog.path)))
            if not dialog.name or not dialog.desc or not dialog.platform or not dialog.path:
                self.show_error_dialog(_("All values must be specified"))
                continue
            if name in self.sdk.projects:
                self.show_error_dialog(_("Project already exists with the name: %s") % name)
                continue
            # If the path specified doesn't exist yet, then that is okay.
            if not os.path.exists(path):
                break
            if not os.path.isdir(path):
                self.show_error_dialog(_("Path: %s exists but is not a directory") % path)
                continue
            # Make sure that the directory specified is empty
            if len(os.listdir(path)):
                self.show_error_dialog(_("Path: %s is a directory which is NOT empty") % path)
                continue
            break
        if result == gtk.RESPONSE_OK:
            try:
                progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                progress_dialog = progress_tree.get_widget('ProgressDialog')
                progress_dialog.set_size_request(450, 250)
                progress_dialog.connect('delete_event', self.ignore)
                progress_tree.get_widget('progress_label').set_text(_("Please wait while installing %s") % dialog.name)
                self.progressbar = progress_tree.get_widget('progressbar')
                self.statuslabel = progress_tree.get_widget('status_label')
                self.progressCancel = progress_tree.get_widget('progressCancel')
                self.progressCancel.set_sensitive(True)
                cancelData = ("AddProject", "Hard")
                self.progressCancel.connect("clicked", self.stop_progress, cancelData)           
                while gtk.events_pending():
                    gtk.main_iteration(False)
                platformName = dialog.platform.split()[0]
                try:
                    if mic_cfg.config.get('general', 'use_rootstraps') == '1':
                        proj = self.sdk.create_project(dialog.path, dialog.name, dialog.desc, self.sdk.platforms[platformName])
                    else:
                        proj = self.sdk.create_project(dialog.path, dialog.name, dialog.desc, self.sdk.platforms[platformName], False)
                except ValueError:
                    print _("Project Creation cancelled")
                    progress_dialog.destroy()
                    return
                if proj.install() == False:
                    print _("Project Creation cancelled")
                    progress_dialog.destroy()
                    try:
                        print _("Trying to cleanup")
                        self.sdk.delete_project(dialog.name)
                    except:
                        print _("could not cleanup project")
                        # if the project creation failed before the list of
                        # projects has been updated, then we expect failure here
                        pass
                    return
                self.projectList.append((dialog.name, dialog.desc, dialog.path, platformName))
                
                progress_dialog.destroy()
                if target_name != None:
                    mic_cmd = 'image-creator --command=create-target --project-name=\'' + dialog.name + '\' --target-name=\'' + target_name + '\''
                    self.cmd_history.append(mic_cmd)
                    self.create_new_target(proj, target_name)

                self.refreshProjectList()
                self.makeActiveProject(dialog.name)
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog("%s" % (sys.exc_info))
                try:
                    self.sdk.delete_project(dialog.name)
                except:
                    # if the project creation failed before the list of
                    # projects has been updated, then we expect failure here
                    pass
                progress_dialog.destroy()

    def on_about_activate(self, event):
        dialog = gtk.AboutDialog()
        dialog.set_name('Moblin Image Creator')
        dialog.set_version(self.sdk.version)
        dialog.set_comments(_("A tool for building Mobile and/or Single Purpose Linux Device Stacks"))
        try:
            f = open(os.path.join(self.sdk.path, "COPYING"), "r")
            dialog.set_license(f.read())
            f.close()
        except:
            traceback.print_exc()
            pass
        dialog.set_copyright("Copyright 2007 by Intel Corporation.  Licensed under the GPL version 2")
        dialog.set_website('http://www.moblin.org/')
        dialog.set_website_label('Mobile & Internet Linux Project')
        dialog.run()
        dialog.destroy()

    def on_projectDelete_clicked(self, event):
        """Delete a Project"""
        model, treePathList = self.projectView.get_selection().get_selected_rows()
        deleteConfirmationText = _("Delete Project(s)?\n")
        for item in treePathList:
            deleteConfirmationText += " %s " % model[item][0]
        tree = gtk.glade.XML(self.gladefile, 'qDialog')
        tree.get_widget('queryLabel').set_text(deleteConfirmationText)
        dialog = tree.get_widget('qDialog')
        result = dialog.run()
        dialog.destroy()       
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            self.progressbar = progress_tree.get_widget('progressbar')
            while gtk.events_pending():
                gtk.main_iteration(False)
            try:
                for item in treePathList:
                    project = self.sdk.projects[model[item][0]]
                    progress_tree.get_widget('progress_label').set_text(_("Please wait while deleting %s") % project.name)
                    mic_cmd = 'image-creator --command=delete-project --project-name=\'' + project.name + '\''
                    self.append_cmd_list(mic_cmd)
                    self.sdk.delete_project(project.name)
                self.remove_current_project()
            except pdk_utils.ImageCreatorUmountError, e:
                self.show_umount_error_dialog(e.directory_set)
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            self.redraw_target_view()
            progress_dialog.destroy()

    def on_new_target_add_clicked(self, widget):
        target_name = ""
        # Open the "New Target" dialog
        while True:
            widgets = gtk.glade.XML(self.gladefile, 'nt_dlg')
            widgets.get_widget('nt_name').set_text(target_name)
            dialog = widgets.get_widget('nt_dlg')
            dialog.set_default_response(gtk.RESPONSE_OK)
            result = dialog.run()
            target_name = widgets.get_widget('nt_name').get_text()
            target_name = target_name.strip()
            dialog.destroy()
            if result == gtk.RESPONSE_OK:
                if not target_name:
                    self.show_error_dialog(_("Must specify a target name"))
                elif target_name in self.current_project().targets:
                    self.show_error_dialog(_("Target: %s already exists") % target_name)
                elif re.search(r'[^-_a-zA-Z0-9]', target_name):
                    target_name = re.sub(r'[^-_a-zA-Z0-9]', '', target_name)
                    self.show_error_dialog(_("Target names can only contain alpha/numeric characters, hyphen and underscore"))
                else:
                    self.create_new_target(self.current_project(), target_name)
                    break
            else:
                break

    def create_new_target(self, project, target_name):
        progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
        progress_dialog = progress_tree.get_widget('ProgressDialog')
        progress_dialog.connect('delete_event', self.ignore)
        progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % target_name)
        self.progressbar = progress_tree.get_widget('progressbar')
        while gtk.events_pending():
            gtk.main_iteration(False)
        if mic_cfg.config.get('general', 'use_rootstraps') == '1':
            project.create_target(target_name)
        else:
            project.create_target(target_name, False)
        self.redraw_target_view()
        progress_dialog.destroy()


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
                    for conflict in fset['conflicts']:
                        if conflict == item[0]:
                            self.fsetTouple[i][1].set_active(False)
                            self.fsetTouple[i][1].set_sensitive(False)                    
                            self.fsetTouple[i] = (self.fsetTouple[i][0], self.fsetTouple[i][1], False, self.fsetTouple[i][3])
                            if self.fsetTouple[i][1].get_label().find("Conflicts: ") != 0:
                                self.fsetTouple[i][1].set_label("Conflicts: " + self.fsetTouple[i][1].get_label())
                i = i + 1
            i = 0
            for item in self.fsetTouple:
                if fSetName != item[0]:
                    for dep in fset['deps']:
                        if dep == item[0]:
                            if self.fsetTouple[i][1].get_active() == False:
                                self.fsetTouple[i][1].set_active(True)
                                #set_active causes this function to be called recurssively
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

            i = 0
            for item in self.fsetTouple:                
                if fSetName != item[0]:
                    for conflict in fset['conflicts']:
                        if conflict == item[0]:
                            self.fsetTouple[i][1].set_sensitive(True)                    
                            self.fsetTouple[i] = (self.fsetTouple[i][0], self.fsetTouple[i][1], False, self.fsetTouple[i][3])
                            if self.fsetTouple[i][1].get_label().find("Conflicts: ") == 0:
                                self.fsetTouple[i][1].set_label(self.fsetTouple[i][1].get_label().split("Conflicts: ")[1])
                i = i + 1


    def setup_fsets_dialog(self, widget, platformName, showFsets = ""):
        tree = gtk.glade.XML(self.gladefile, 'fsetsDialog')
        dialog = tree.get_widget('fsetsDialog')
        vbox = tree.get_widget('vbox')
        checkbox = tree.get_widget('debug-check-button')
        fsetToInstall = []
        debug_pkgs = False
  
        platform = self.sdk.platforms[platformName]
        self.currentPlatformSelected = platform
        #platform = self.current_project().platform
        all_fsets = set(platform.fset)
        if showFsets == "all":
            installed_fsets = set()
        else:
            installed_fsets = set(self.current_target().installed_fsets())
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
            toolTipText = _("<b>Depends on FSet(s):</b> ")
            for depends in sorted(platform.fset[fset_name].deps):
                toolTipText += " %s " % depends
            toolTipText += _("\n<b>Debug Packages:</b> ")
            for debug_pkgs in sorted(platform.fset[fset_name].debug_pkgs):
                toolTipText += " %s " % debug_pkgs
            toolTipText += _("\n<b>Packages:</b> ")
            for pkgs in sorted(platform.fset[fset_name].pkgs):
                toolTipText += " %s " % pkgs
            if self.pygtkOldVersion == False:
                self.fsetTouple[i][1].set_tooltip_markup(toolTipText)
            for installedFset in installed_fsets:
                for conflict in platform.fset[installedFset]['conflicts']:
                    if conflict == fset_name:
                        self.fsetTouple[i][1].set_sensitive(False)
                        self.fsetTouple[i][1].set_label("Conflicts: " + self.fsetTouple[i][1].get_label())
            i += 1
        if not iter:
            self.show_error_dialog(_("Nothing available to install!"))
            dialog.destroy()
            return
        self.fsetTouple.pop(0)
        i = 0
        for checkBox in self.fsetTouple:
            checkBox[1].connect("clicked", self.checkBoxCallback, self.fsetTouple[i][0])
            vbox.pack_start(checkBox[1])
            i = i + 1

        dialog.show_all()
        while True:
            if dialog.run() == gtk.RESPONSE_OK:
                debug_pkgs = checkbox.get_active()
                numFsetsToInstall = 0
                for fsetName in self.fsetTouple:
                        if fsetName[2] == True:
                            numFsetsToInstall = numFsetsToInstall + 1
                print _("Number of fsets to install: %s") % numFsetsToInstall

                if numFsetsToInstall != 0:
                    dialog.destroy()
                    for fsetName in self.fsetTouple:
                        if fsetName[2] == True:
                            fsetToInstall.append(fsetName[0])
                    break
                else:
                    print _("No fset selected")
                    self.show_error_dialog(_("Please Choose an Fset"))
            else:
                break
        dialog.destroy()
        return (fsetToInstall, debug_pkgs)

    def on_install_group(self, widget):
        self.gladefile = os.path.join(self.sdk.path, "image-creator.glade")
        progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
        progress_dialog = progress_tree.get_widget('ProgressDialog')
        progress_dialog.connect('delete_event', self.ignore)
        self.progressbar = progress_tree.get_widget('progressbar')
        progress_tree.get_widget('progress_label').set_text(_("Getting Group List..."))

        packageGroup = package_group.packageGroup(self.sdk, self.current_target())
        groupList = packageGroup.run()
        if groupList:
            progress_tree.get_widget('progress_label').set_text(_("Installing Groups..."))
            self.current_target().installGroup(groupList)
        progress_dialog.destroy()


    def on_install_fset(self, widget):
        platformName = self.current_project().platform.name
        fsetsToInstall, debug_pkgs = self.setup_fsets_dialog(widget, platformName)
        if fsetsToInstall:
            print _("Debug packages = %s") % debug_pkgs
            platform = self.current_project().platform
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            self.progressbar = progress_tree.get_widget('progressbar')
            for fsetName in fsetsToInstall:
                #print _("Installing: %s") % fset    
                fset = platform.fset[fsetName]
                print _("Installing fset %s.................\n") % fsetName
                progress_tree.get_widget('progress_label').set_text(_("Please wait while installing %s") % fset.name)
                try:
                    mic_cmd = 'image-creator --command=install-fset --platform-name=\'' + platformName + '\' --project-name=\'' + self.current_project().name + '\' --target-name=\'' + self.current_target().name + '\' --fset=\'' + fsetName + '\''
                    if debug_pkgs:
                        mic_cmd = mic_cmd + ' --enable-debug'
                    self.append_cmd_list(mic_cmd)

                    self.current_target().installFset(fset, fsets = platform.fset, debug_pkgs = debug_pkgs)
                except ValueError, e:
                    self.show_error_dialog(e.args[0])
                except:
                    traceback.print_exc()
                    if debug: print_exc_plus()
                    self.show_error_dialog(_("Unexpected error: %s") % (sys.exc_info()[1]))
            self.redraw_target_view()
            progress_dialog.destroy()

    def ignore(self, *args):
        return True

    def set_status_label(self, newLabel):
        print _("Setting new status label: %s") % newLabel
        self.statuslabel.set_text(_("Current action: %s") % newLabel)

    def gui_throbber(self, process):
        self.progressbar.pulse()
        while gtk.events_pending():
            gtk.main_iteration(False)
        time.sleep(0.01)

    def fset_install_updated(self, box, label, platform, checkbox):
        fset = platform.fset[box.get_active_text()]
        checkbox.set_sensitive(True)
        label.set_text(fset.desc)

    def on_delete_target_clicked(self, widget):
        model, treePathList = self.targetView.get_selection().get_selected_rows()
        deleteConfirmationText = _("Delete Target(s)?\n")
        for item in treePathList:
            deleteConfirmationText += " %s " % model[item][0]
        tree = gtk.glade.XML(self.gladefile, 'qDialog')
        tree.get_widget('queryLabel').set_text(deleteConfirmationText)
        dialog = tree.get_widget('qDialog')
        dialog.set_title(_("Delete Target"))
        result = dialog.run()
        dialog.destroy()       
        if result == gtk.RESPONSE_OK:    
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            self.progressbar = progress_tree.get_widget('progressbar')
            while gtk.events_pending():
                gtk.main_iteration(False)
            try:
                project = self.current_project()
                for item in treePathList:
                    target = self.current_project().targets[model[item][0]]
                    progress_tree.get_widget('progress_label').set_text(_("Please wait while deleting %s") % target.name)
                    mic_cmd = 'image-creator --command=delete-target --project-name=\'' + self.current_project().name + '\' --target-name=\'' + target.name +'\''
                    self.append_cmd_list(mic_cmd)
                    self.sdk.projects[project.name].delete_target(target.name, callback = self.gui_throbber)
                self.remove_current_target()
            except pdk_utils.ImageCreatorUmountError, e:
                self.show_umount_error_dialog(e.directory_set)
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            self.redraw_target_view() 
            progress_dialog.destroy()

    def current_project(self):
        num_rows_selected = self.projectView.get_selection().count_selected_rows()
        if num_rows_selected == 1:
            model, treePathList = self.projectView.get_selection().get_selected_rows()
            return self.sdk.projects[model[treePathList[0]][0]]
        else:
            #Return None if more than one project is selected
            return None

    def current_target(self):
        num_rows_selected = self.targetView.get_selection().count_selected_rows()
        if num_rows_selected == 1:
            model, treePathList = self.targetView.get_selection().get_selected_rows()
            return self.current_project().targets[model[treePathList[0]][0]]
        else:
            #Return None if more than one project is selected
            return None

    def remove_current_project(self):
        model, treePathList = self.projectView.get_selection().get_selected_rows()
        treePathList.reverse()
        #Do not want project_view_changed handler to execute while deleting projects
        self.projectView.get_selection().handler_block(self.projectView_handler)
        for item in treePathList:
            self.projectView.get_selection().unselect_path(item)
            self.projectList.remove(self.projectList.get_iter(item))
        self.projectView.get_selection().handler_unblock(self.projectView_handler)
        #We dont really need to remove the items since refreshProjectList clears the list 
        #and repopulates it
        #FIXME
        self.refreshProjectList()

    def remove_current_target(self):
        model, treePathList = self.targetView.get_selection().get_selected_rows()
        treePathList.reverse()
        #Do not want target_view_changed handler to execute while deleting targets
        self.targetView.get_selection().handler_block(self.targetView_handler)
        for item in treePathList:
            self.targetView.get_selection().unselect_path(item)
            self.targetList.remove(self.targetList.get_iter(item))
        self.targetView.get_selection().handler_unblock(self.targetView_handler)

    def show_error_dialog(self, message= _("An unknown error has occurred!")):
        widgets = gtk.glade.XML(self.gladefile, 'error_dialog')
        widgets.get_widget('error_label').set_text(message)
        dialog = widgets.get_widget('error_dialog')
        dialog.run()
        dialog.destroy()

    def show_umount_error_dialog(self, directory_list = []):
        widgets = gtk.glade.XML(self.gladefile, 'error_dialog_umount')
        #widgets.get_widget('error_label').set_text(_("Could not unmount the following directories:"))
        dirTree = widgets.get_widget('umount_dirs')
        dialog = widgets.get_widget('error_dialog_umount')
        dirList = gtk.ListStore(gobject.TYPE_STRING)
        cellRenderC0 = gtk.CellRendererText()
        col0 = gtk.TreeViewColumn(_("Directory List"), cellRenderC0)
        dirTree.append_column(col0)
        col0.add_attribute(cellRenderC0, 'text', 0)
        col0.set_resizable(True)
        for dirname in directory_list:
            dirList.append([dirname])
        dirTree.set_model(dirList)
        dialog.run()
        dialog.destroy()

    def on_term_launch_clicked(self, widget):
        project_path = self.current_project().path
        project_name = self.current_project().name
        prompt_file = open(os.path.join(project_path, "etc/debian_chroot"), 'w')
        print >> prompt_file, "P: %s" % project_name
        prompt_file.close()
        print _("Project path: %s") % project_path
        cmd = '/usr/bin/gnome-terminal -x /usr/sbin/chroot %s env -u SHELL HOME=/root su -p - &' % (project_path)
        print cmd
        if os.system(cmd) != 0:
            print _("gnome-terminal may not be present. Trying xterm")    
            cmd = '/usr/bin/xterm -e /usr/sbin/chroot %s env -u SHELL HOME=/root sh &' % (project_path)
            os.system(cmd)


    def on_target_term_launch_clicked(self, widget):
        project_path = self.current_project().path
        target = self.current_target()
        target.mount()
        target_path= "%s/targets/%s/fs" % (project_path, target.name)
        prompt_file = open(os.path.join(target_path, "etc/debian_chroot"), 'w')
        print >> prompt_file, "T: %s" % target.name
        prompt_file.close()
        print _("Target path: %s") % target_path
        cmd = '/usr/bin/gnome-terminal -x /usr/sbin/chroot %s env -u SHELL HOME=/root su -p - &' % (target_path)
        print cmd
        if os.system(cmd) != 0:
            print _("gnome-terminal may not be present. Trying xterm")    
            cmd = '/usr/bin/xterm -e /usr/sbin/chroot %s env -u SHELL HOME=/root sh &' % (project_path)
            os.system(cmd)

    def on_target_config_clicked(self, widget):
        project_path = self.current_project().path
        target = self.current_target()
        widgets = gtk.glade.XML(self.gladefile, 'target_config_dlg')
        dialog = widgets.get_widget('target_config_dlg')
        current_target = {}
        for config in self.current_project().platform.target_configs:
            current_target[config] = widgets.get_widget(config)
            config_value = self.current_project().get_target_config(target.name, config)
            if not config_value:
                print _("%s: Using default parametor.") % config
                config_value = self.current_project().platform.target_configs[config]
            if isinstance(current_target[config], gtk.Entry) or \
                isinstance(current_target[config], gtk.SpinButton):
                current_target[config].set_text(config_value)
            elif isinstance(current_target[config], gtk.CheckButton) or \
                isinstance(current_target[config], gtk.ComboBox):
                current_target[config].set_active(int(config_value))
            else:
                try:
                    current_target[config].set_text(config_value)
                except:
                    pass
        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            for config in self.current_project().platform.target_configs:
                if isinstance(current_target[config], gtk.Entry) or \
                    isinstance(current_target[config], gtk.SpinButton):
                    self.current_project().set_target_config(target.name, config, current_target[config].get_text())
                elif isinstance(current_target[config], gtk.CheckButton) or \
                    isinstance(current_target[config], gtk.ComboBox):
                    self.current_project().set_target_config(target.name, config, int(current_target[config].get_active()))
                else:
                    try:
                        self.current_project().set_target_config(target.name, config, current_target[config].get_text())
                    except:
                        pass
        dialog.destroy()

    def on_liveUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-live-usb --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_live_usb(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_liveRWUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-live-usbrw --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_live_usb(target.name, img_name, 'EXT3FS')
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_NFSliveUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-nfslive-usb --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_nfslive_usb(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_installUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-install-usb --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_install_usb(target.name, img_name)
            except ValueError, e:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_liveCD_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName(default_name=".iso")
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-live-iso --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_live_iso(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_NFSliveCD_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName(default_name=".iso")
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-nfslive-iso --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_nfslive_iso(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_installCD_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName(default_name=".iso")
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-install-iso --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_install_iso(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()
 
    def on_NAND_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        result, img_name = self.getImageName(default_name=".bin")
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                mic_cmd = 'image-creator --command=create-nand --project-name=\'' + project.name + '\' --target-name=\'' + target.name + '\' --image-name=\'' + img_name + '\''
                self.append_cmd_list(mic_cmd)
                self.current_project().create_NAND_image(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog()
            progress_dialog.destroy()


    def on_launch_vm_clicked(self, widget):
        # check whether the shared image exists
        # the path of folder containing this image is fixed and hardcoded
        kvm_dir = paths.LOCALSTATEDIR + '/lib/moblin-image-creator/kvm'
        kvmimg_file = os.path.join(kvm_dir, 'mic_vm_share.img')
        if os.path.exists (kvm_dir) == False:
            print _("Creating directory %s ... ") % kvm_dir
            cmd = 'mkdir ' + kvm_dir
            os.popen(cmd)
        if os.path.isfile(kvmimg_file) == False:
            print _("Creating image %s ... ") % kvmimg_file
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while creating shared image..."))
            self.progressbar = progress_tree.get_widget('progressbar')
            cmd = "qemu-img create %s -f qcow2 4G" % kvmimg_file
            pdk_utils.execCommand(cmd, False, None, self.gui_throbber)
            progress_dialog.destroy()
        # select a live usb image        
        target = self.current_target()
        dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_OPEN, title=_("Choose a Live USB image"))
        dialog.set_current_folder(target.top + "/image/")
        dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        filter_image = gtk.FileFilter()
        filter_image.set_name("Image files");
        filter_image.add_pattern("*.img");
        dialog.add_filter(filter_image);
        filter_any = gtk.FileFilter();
        filter_any.set_name("Any files");
        filter_any.add_pattern("*");
        dialog.add_filter(filter_any);
        if dialog.run() == gtk.RESPONSE_OK:
            live_img = dialog.get_filename()
            dialog.destroy()
        else:
            dialog.destroy()
            return
        # boot the live usb image in KVM in background
        kvm_dev = os.path.lexists('/dev/kvm')
        qemu_bin = "qemu"
        if mic_cfg.config.get('general', 'package_manager') == 'apt':
            if kvm_dev:
                qemu_bin = "kvm"
        elif mic_cfg.config.get('general', 'package_manager') == 'yum':
            if kvm_dev:
                qemu_bin = "qemu-kvm"

        os.popen(qemu_bin +" -no-acpi -m 512 -hda " + live_img + " -hdb " + paths.LOCALSTATEDIR + "/lib/moblin-image-creator/kvm/mic_vm_share.img -boot c &")

    def getImageName(self, default_name = ".img"):
        """Function to query the user for the name of the image file they want
        to create"""
        #default_name = ".img"
        while True:
            widgets = gtk.glade.XML(self.gladefile, 'new_img_dlg')
            dialog = widgets.get_widget('new_img_dlg')
            dialog.set_default_response(gtk.RESPONSE_OK)
            widgets.get_widget('img_name').set_text(default_name)
            result = dialog.run()
            img_name = widgets.get_widget('img_name').get_text()
            dialog.destroy()
            default_name = img_name
            if result != gtk.RESPONSE_OK:
                break
            if img_name and img_name != ".img":
                break
        return (result, img_name)

    def writeUsbImageHelper(self, directory):
        """Given a directory name, prompt the user to select an image file from
        the directory and then prompt the user to select the USB device to
        write the image file to, and then write the image."""
        dialog = gtk.FileChooserDialog('Select Image File', None, gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK), None)
        dialog.set_current_folder(directory)
        result = dialog.run()
        if result == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            print _("No target image selected!")
            return False
        elif result == gtk.RESPONSE_OK:
            image_filename = dialog.get_filename()
            dialog.destroy()
            print _("Selected file name: %s ") % image_filename
            widgets = gtk.glade.XML(self.gladefile, 'select_usb_disk_dialog')
            dialog2 = widgets.get_widget('select_usb_disk_dialog')
            usb_dev_list = gtk.ListStore(gobject.TYPE_STRING)
            usb_disk_list = pdk_utils.get_current_udisks()
            if not usb_disk_list:
                dialog2.destroy()
                self.show_error_dialog('No USB disk detected! Please plug in your USB disk and try again!')
                return False
            for iter_dev in usb_disk_list:
                iter_obj = usb_dev_list.append([iter_dev])
            usb_disks = widgets.get_widget('usb_disks')
            column = gtk.TreeViewColumn('Your current USB disks', gtk.CellRendererText(), text=0)
            column.set_resizable(True)
            column.set_sort_column_id(0)
            usb_disks.append_column(column)
            usb_disks.set_model(usb_dev_list)
            usb_disks.get_selection().select_iter(iter_obj)
            result = dialog2.run()
            return_code = False
            if result == gtk.RESPONSE_CANCEL:
                dialog2.destroy()
                print _("No USB device selected!")
            elif result == gtk.RESPONSE_OK:
                model, iter = usb_disks.get_selection().get_selected()
                dialog2.destroy()
                if not iter:
                    self.show_error_dialog('No USB disk selected!')
                else:
                    usb_disk = model[iter][0]
                    print _("Selected USB disk %s") % usb_disk
                    if not pdk_utils.umount_device(usb_disk):
                        self.show_error_dialog(_("Can not umount %s. Please close any shells or opened files still under mount point and try again!") % usb_disk)
                        return_code = False
                    else:
                        progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                        progress_dialog = progress_tree.get_widget('ProgressDialog')
                        progress_dialog.connect('delete_event', self.ignore)
                        progress_tree.get_widget('progress_label').set_text(_("Please wait while writing image to USB disk"))
                        self.progressbar = progress_tree.get_widget('progressbar')
                        print _("Writing image to USB disk %s") % usb_disk
                        cmd = "dd bs=4096 if=%s of=%s" % (image_filename, usb_disk)
                        result = pdk_utils.execCommand(cmd, False, None, self.gui_throbber)
                        progress_dialog.destroy()
                        if result != 0:
                            self.show_error_dialog(_("Error writing to USB drive.  'dd' returned code: %s") % result)
                            return_code = False
                        else:
                            return_code = True
                        print _("Writing Complete")
                        return_code = True
            return return_code

    def writeUsbImage(self, widget):
        """Query the user to select an image file from the images directory in
        the target, then write that image to the USB flash drive"""
        project_path = self.current_project().path
        target = self.current_target()
        target_path= "%s/targets/%s/image" % (project_path, target.name)
        return self.writeUsbImageHelper(target_path)

    def on_WriteUsbImage_activate(self, widget):
        home_dir = os.getenv("HOME")
        return self.writeUsbImageHelper(home_dir)

    def on_ClearRootstraps_activate(self, widget):
        print _("In on_ClearRootstraps_activate")
        progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
        progress_dialog = progress_tree.get_widget('ProgressDialog')
        progress_dialog.connect('delete_event', self.ignore)
        progress_tree.get_widget('progress_label').set_text(_("Please wait while clearing rootstraps"))
        self.progressbar = progress_tree.get_widget('progressbar')

        self.sdk.clear_rootstraps()

        progress_dialog.destroy()

    def on_Load_activate(self, widget):
        print _("In on_Load_activate")
        dialog = gtk.Dialog(_("Provide a Project Name"), None, gtk.DIALOG_MODAL,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_size_request(300, 150)
        projectNameEntry = gtk.Entry(100)
        projectNameEntry.set_has_frame(True)
        projectNameEntry.set_activates_default(True)
        #projectNameEntry.set_text(_("Enter Project Name Here"))
        dialog.vbox.pack_start(projectNameEntry)
        dialog.show_all()
        obtainedUniqueName = False
        projectExistsLabel = gtk.Label("")
        dialog.vbox.pack_start(projectExistsLabel)
        projectName = ""
        while obtainedUniqueName == False:
            dialog.show_all()
            result = dialog.run()
            if result == gtk.RESPONSE_CANCEL:
                print _("No Project Name")
                break
            if result == gtk.RESPONSE_OK:
                projectName = projectNameEntry.get_text()
                if projectName == "":
                    print _("Project Name is blank")
                    dialog.set_size_request(300, 150)
                    projectExistsLabel.set_markup(_("<b><span foreground=\"red\">Please provide a project name</span></b>"))
                else:
                    print _("Project name: %s") % projectName
                    projectNameExists = False
                    for key in sorted(self.sdk.projects.iterkeys()):
                        p = self.sdk.projects[key]
                        if p.name == projectName:
                            projectNameExists = True
                            print _("Project %s already exists") % projectName
                            dialog.set_size_request(400, 150)
                            projectExistsLabel.set_markup(_("<b><span foreground=\"red\">Project %s already exists.</span></b>") % projectName)
                            break
                    if projectNameExists == False:
                        obtainedUniqueName = True

        dialog.destroy()

        if obtainedUniqueName == True:
            dialog = gtk.FileChooserDialog('Select Image File',None,gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK),None)
            fileFilter = gtk.FileFilter()
            fileFilter.set_name(".mic.tar.bz2")
            fileFilter.add_pattern("*.mic.tar.bz2")
            dialog.add_filter(fileFilter)
            result = dialog.run()
            if result == gtk.RESPONSE_CANCEL:
                dialog.destroy()
                print _("No target image selected!")
            if result == gtk.RESPONSE_OK:
                fileToLoad=dialog.get_filename()
                print _("Selected file name: %s ") % fileToLoad
                dialog.destroy()
                dialog = gtk.FileChooserDialog('Choose the destination Folder',None,gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK),None)
                result = dialog.run()
                if result == gtk.RESPONSE_CANCEL:
                    print _("No Destination Folder")
                    dialog.destroy()
                if result == gtk.RESPONSE_OK:
                    targetFolder = dialog.get_filename()
                    print _("Targer File Name: %s") % (targetFolder)
                    dialog.destroy()

                    progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                    progress_dialog = progress_tree.get_widget('ProgressDialog')
                    progress_dialog.connect('delete_event', self.ignore)
                    progress_tree.get_widget('progress_label').set_text(_("Please wait while loading Project: %s") % projectName)
                    self.progressbar = progress_tree.get_widget('progressbar')

                    print _("Loading Project %s") % projectName
                    self.sdk.load_project(projectName, targetFolder, fileToLoad, self.gui_throbber)
                    print _("Loading Project Complete")
                    progress_dialog.destroy()
                    self.refreshProjectList()

    def refreshProjectList(self):
        self.sdk.discover_projects()
        self.projectList.clear()
        for key in sorted(self.sdk.projects.iterkeys()):
            p = self.sdk.projects[key]
            self.projectList.append((p.name, p.desc, p.path, p.platform.name))
        self.projectView.set_model(self.projectList)

    def makeActiveProject(self, project_name):
        selection = self.projectView.get_selection()
        for count, row in enumerate(self.projectList):
            name = row[0]
            if name == project_name:
                selection.select_path(count)
                self.redraw_target_view()
                break

    def on_Save_activate(self, widget):
        print _("In on_Save_activate")
        dialog = gtk.Dialog(_("Choose Project to Save"), None, gtk.DIALOG_MODAL,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_size_request(300, 100)
        currentProjectList = gtk.ListStore(str, str)
        projectList = gtk.combo_box_new_text()
        for key in sorted(self.sdk.projects.iterkeys()):
            p = self.sdk.projects[key]
            projectList.append_text(p.name)
        projectList.set_active(0)
        dialog.vbox.pack_start(projectList)
        dialog.show_all()
        result = dialog.run()
        if result == gtk.RESPONSE_CANCEL:
            print _("No Project Name")
            dialog.destroy()
        if result == gtk.RESPONSE_OK:
            projectNameToSave = projectList.get_active_text()
            print _("Project name to Save: %s") % (projectNameToSave)
            dialog.destroy()
            dialog = gtk.FileChooserDialog('Choose the destination File Name',None,gtk.FILE_CHOOSER_ACTION_SAVE,
                (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK),None)
            result = dialog.run()
            if result == gtk.RESPONSE_CANCEL:
                print _("No Project Name")
                dialog.destroy()
            if result == gtk.RESPONSE_OK:
                targetFileName = dialog.get_filename()
                print _("Targer File Name: %s") % (targetFileName)
                dialog.destroy()

                progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                progress_dialog = progress_tree.get_widget('ProgressDialog')
                progress_dialog.connect('delete_event', self.ignore)
                progress_tree.get_widget('progress_label').set_text(_("Please wait while saving Project: %s") % projectNameToSave)
                self.progressbar = progress_tree.get_widget('progressbar')

                while gtk.events_pending():
                    gtk.main_iteration(False)
                print _("Saving Project %s") % projectNameToSave
                self.sdk.save_project(projectNameToSave, targetFileName)
                print _("Saving Complete")
                progress_dialog.destroy()

    def on_upgrade_project_clicked(self, widget):
        progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
        progress_dialog = progress_tree.get_widget('ProgressDialog')
        progress_dialog.connect('delete_event', self.ignore)
        progress_tree.get_widget('progress_label').set_text(_("Please wait while upgrading Project"))
        self.progressbar = progress_tree.get_widget('progressbar')
        mic_cmd='image-creator --command=update-project --project-name=\'' + self.current_project().name + '\''
        self.append_cmd_list(mic_cmd)
        result = self.current_project().updateAndUpgrade()
        if result != 0:
             raise OSError(_("Internal error while attempting to run update/upgrade: %s") % result)
        progress_dialog.destroy()


    def on_upgrade_target_clicked(self, widget):
        progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
        progress_dialog = progress_tree.get_widget('ProgressDialog')
        progress_dialog.connect('delete_event', self.ignore)
        progress_tree.get_widget('progress_label').set_text(_("Please wait while upgrading Target"))
        self.progressbar = progress_tree.get_widget('progressbar')
        mic_cmd='image-creator --command=update-target --project-name=\'' + self.current_project().name + '\' --target-name=\'' + self.current_target().name + '\''
        self.append_cmd_list(mic_cmd)
        result = self.current_target().updateAndUpgrade()
        if result != 0:
             raise OSError(_("Internal error while attempting to run update/upgrade: %s") % result)
        progress_dialog.destroy()
        self.redraw_target_view()

    def on_editRepo_clicked(self, widget):
        editRepo = repo_editor.repoEditor(self.sdk, os.path.join(self.current_target().path, "etc/yum.repos.d"))
        editRepo.run()
        

    def formatMirrorSection(self, sectionName, sectionSearch, sectionReplace):
        sectionTextFormatted = "\n%s = [\n" % sectionName
        index = 0
        for line in sectionSearch:
                sectionTextFormatted += "\t(r'%s','%s'),\n" % (sectionSearch[index], sectionReplace[index])
                index += 1
        sectionTextFormatted += "]"
        return sectionTextFormatted

    def saveMirrorConfigFile(self, saveType, sectionName, sectionText):
        comments = """#!/usr/bin/python
    # If you have a local mirror of the Ubuntu and/or Moblin.org APT repositories,
    # then this configuration file will be useful to you.

    # This file is used when copying the files that will go into
    # /etc/apt/sources.list.d/  It consists of a list, which contains a search
    # regular expression and a replacement string.  When copying the files into the
    # /etc/apt/sources.list.d/ , of the projects and targets, a search and replace
    # will be performed.

    #sources_regex = [
        # source_archive,                           local mirror of source archive

    # Edit the following and uncomment them to enable use of a local mirror server.
    # NOTE: The trailing space is important in the strings!!!!
    #    (r'http://archive.ubuntu.com/ubuntu ',       'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_ARCHIVES_UBUNTU_COM/ '),
    #    (r'http://ports.ubuntu.com/ubuntu-ports ', 'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_PORTS_UBUNTU_COM/ '),
    #    (r'http://www.moblin.org/apt ',       'http://<PATH_TO_YOUR_LOCAL_MIRROR_OF_MOBLIN_ORG/ '),

    #]"""
        configFile = os.path.join(os.path.expanduser("~/.image-creator"), "sources_cfg")
        #if saveType == "saveSection":
        #if saveType == "add":
        if saveType == "save":
            if os.path.isfile(configFile):
                f = open(configFile, "w")
                if self.noMirror.get_active() == True:
                    f.write("use_mirror=\"no_mirror\"\n")
                else:
                    f.write("use_mirror=\"%s\"\n" % self.mirrorSelection.get_active_text())
                f.write(comments)
                for mirrorListItem in self.global_dict:
                    sectionSearch = []
                    sectionReplace = []
                    if mirrorListItem != '__builtins__':
                        if mirrorListItem != 'use_mirror':
                            sectionData = ""
                            sectionDataList = self.global_dict[mirrorListItem]
                            for item in sectionDataList:
                                sectionSearch.append(item[0])
                                sectionReplace.append(item[1])
                            f.write(self.formatMirrorSection(mirrorListItem, sectionSearch, sectionReplace))
                f.close()

    def mirrorSettings_callback(self, widget, buttonName):
        if buttonName == "nomirror":
            self.mirrorSelection.set_active(-1)
            self.mirrorSelection.set_sensitive(False)
            self.mirrorDetailsList = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
            self.mirrorDetails.set_model(self.mirrorDetailsList)
            self.mirrorDetails.set_sensitive(False)

        else:
            self.mirrorSelection.set_sensitive(True)
            self.mirrorDetails.set_sensitive(True)
            currentMirror = self.getCurrentMirror()
            if currentMirror == "no_mirror":
                self.mirrorSelection.set_active(0)
            else:
                self.mirrorSelection.set_active(self.mirrorSelectionList[currentMirror])

    def mirrorSelection_callback(self, widget):
        selection = self.mirrorSelection.get_active_text()
        if selection in self.global_dict:
            self.mirrorDetailsList = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
            src_regex = self.global_dict[selection]
            for item in src_regex:
                self.mirrorDetailsList.append(None, [item[0], item[1]])
            self.mirrorDetails.set_model(self.mirrorDetailsList)
        if selection == 'Add a Section':
            dialog_tree = gtk.glade.XML(self.gladefile, 'addNewMirror')
            dialog = dialog_tree.get_widget('addNewMirror')
            sectionNameEntry = dialog_tree.get_widget('sectionName')
            mirrorListEntry = dialog_tree.get_widget('mirrorList')
            while True:
                result = dialog.run()
                if result == gtk.RESPONSE_OK:
                    sectionName = sectionNameEntry.get_text()
                    mirrorListBuffer = mirrorListEntry.get_buffer()
                    mirrorList = mirrorListBuffer.get_text(mirrorListBuffer.get_start_iter(), mirrorListBuffer.get_end_iter())
                    if sectionName == "":
                        self.show_error_dialog(_("All fields are required"))
                        continue
                    elif  mirrorList == "":
                        self.show_error_dialog(_("All fields are required"))
                        continue
                    else:
                        self.mirrorSelection_entry_box.append([sectionName])
                        self.saveMirrorConfigFile("add", sectionName, mirrorList)
                        self.populateMirrorSections()
                        self.mirrorSelection.set_active(0)
                        break
                else:
                    break
            dialog.destroy()

    def populateMirrorSections(self):
        configFile = os.path.join(os.path.expanduser("~/.image-creator"), "sources_cfg")
        self.mirrorSelection_entry_box = gtk.ListStore(gobject.TYPE_STRING)
        self.mirrorSelectionList = {}
        if os.path.isfile(configFile):
            self.global_dict = {}
            execfile(configFile, self.global_dict)
            index = 0
            for mirrorListItem in self.global_dict:
                if mirrorListItem != '__builtins__':
                    if mirrorListItem != 'use_mirror':
                        self.mirrorSelectionList[mirrorListItem] = index
                        index += 1
                        self.mirrorSelection_entry_box.append([mirrorListItem])
        self.mirrorSelection.set_model(self.mirrorSelection_entry_box)

    def getCurrentMirror(self):
        configFile = os.path.join(os.path.expanduser("~/.image-creator"), "sources_cfg")
        if os.path.isfile(configFile):
            f = open(configFile, "r")
            mirrorSelectionLine = f.readline()
            f.close()
            if mirrorSelectionLine.find("=") != -1:
                mirrorToUse = mirrorSelectionLine.split('=')[1]
                mirrorToUse = mirrorToUse[1:-2]
                if mirrorToUse in self.global_dict:
                    return mirrorToUse
                else:
                    return "no_mirror"
            else:
                return "no_mirror"
        else:
            return "no_mirror"

    def on_MirrorSettings_activate(self, widget):
        dialog_tree = gtk.glade.XML(self.gladefile, 'mirror')
        dialog = dialog_tree.get_widget('mirror')
        self.noMirror = dialog_tree.get_widget('noMirror')
        self.useMirror = dialog_tree.get_widget('useMirror')
        self.mirrorDetails = dialog_tree.get_widget('mirrorDetails')
        self.noMirror.connect('clicked', self.mirrorSettings_callback, "nomirror")
        self.useMirror.connect('clicked', self.mirrorSettings_callback, "usemirror")

        self.mirrorSelection = dialog_tree.get_widget('mirrorSelection')
        self.mirrorSelection.connect('changed', self.mirrorSelection_callback)
        self.populateMirrorSections()


        cellRenderC0 = gtk.CellRendererText()
        cellRenderC1 = gtk.CellRendererText()
        col0 = gtk.TreeViewColumn(_("Search Expression"), cellRenderC0)
        col1 = gtk.TreeViewColumn(_("Replace Expression"), cellRenderC1)

        self.mirrorDetails.append_column(col0)
        self.mirrorDetails.append_column(col1)

        col0.add_attribute(cellRenderC0, 'text', 0)
        col0.set_resizable(True)
        col1.add_attribute(cellRenderC1, 'text', 1)
        col1.set_resizable(True)

        self.mirrorDetails.set_headers_clickable(True)
        self.mirrorDetailsList = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.mirrorDetails.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.mirrorDetails.set_model(self.mirrorDetailsList)

        currentMirror = self.getCurrentMirror()
        if currentMirror == "no_mirror":
            self.noMirror.set_active(True)
        else:
            self.useMirror.set_active(True)

        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            self.saveMirrorConfigFile("save", None, None)
        dialog.destroy()

    def on_Add_Project_Wizard_activate(self, widget):
        projectAssistantWizard = project_assistant.projectAssistant(self.sdk)
        newProjectConfiguration = projectAssistantWizard.run()
        #print "%s %s %s %s %s %s %s" % (newProjectConfiguration.projectName, newProjectConfiguration.projectDesc, newProjectConfiguration.projectPath, newProjectConfiguration.projectPlatform, newProjectConfiguration.targetName, newProjectConfiguration.fsetsToInstall, newProjectConfiguration.debugPkgs)
        if newProjectConfiguration.projectName and newProjectConfiguration.projectDesc and newProjectConfiguration.projectPath and newProjectConfiguration.projectPlatform and newProjectConfiguration.targetName:
            print _("Creating Project and Target")
            try:
                progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                progress_dialog = progress_tree.get_widget('ProgressDialog')
                progress_dialog.set_size_request(450, 250)
                progress_dialog.connect('delete_event', self.ignore)
                progress_tree.get_widget('progress_label').set_text(_("Please wait while installing %s") % newProjectConfiguration.projectName)
                self.progressbar = progress_tree.get_widget('progressbar')
                self.statuslabel = progress_tree.get_widget('status_label')
                while gtk.events_pending():
                    gtk.main_iteration(False)      
                if mic_cfg.config.get('general', 'use_rootstraps') == '1':
                    proj = self.sdk.create_project(newProjectConfiguration.projectPath, newProjectConfiguration.projectName, newProjectConfiguration.projectDesc, self.sdk.platforms[newProjectConfiguration.projectPlatform])
                else:
                    proj = self.sdk.create_project(newProjectConfiguration.projectPath, newProjectConfiguration.projectName, newProjectConfiguration.projectDesc, self.sdk.platforms[newProjectConfiguration.projectPlatform], False)
                proj.install()
                self.projectList.append((newProjectConfiguration.projectName, newProjectConfiguration.projectDesc, newProjectConfiguration.projectPath, newProjectConfiguration.projectPlatform))
                
                progress_dialog.destroy()
                self.create_new_target(proj, newProjectConfiguration.targetName)
                self.refreshProjectList()
                self.makeActiveProject(newProjectConfiguration.projectName)
            except:
                traceback.print_exc()
                if debug: print_exc_plus()
                self.show_error_dialog("%s" % (sys.exc_info))
                try:
                    self.sdk.delete_project(newProjectConfiguration.projectName)
                except:
                    # if the project creation failed before the list of
                    # projects has been updated, then we expect failure here
                    pass
            progress_dialog.destroy()

            if newProjectConfiguration.fsetsToInstall:
                print _("Installing the following fsets: %s") % newProjectConfiguration.fsetsToInstall
                platform = self.current_project().platform
                progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                progress_dialog = progress_tree.get_widget('ProgressDialog')
                progress_dialog.connect('delete_event', self.ignore)
                self.progressbar = progress_tree.get_widget('progressbar')
                for fsetName in newProjectConfiguration.fsetsToInstall:
                    fset = platform.fset[fsetName]
                    print _("Installing fset %s.................\n") % fsetName
                    progress_tree.get_widget('progress_label').set_text(_("Please wait while installing %s") % fset.name)
                    try:
                        self.current_target().installFset(fset, fsets = platform.fset, debug_pkgs = newProjectConfiguration.debugPkgs)
                    except ValueError, e:
                        self.show_error_dialog(e.args[0])
                    except:
                        traceback.print_exc()
                        if debug: print_exc_plus()
                        self.show_error_dialog(_("Unexpected error: %s") % (sys.exc_info()[1]))
                self.redraw_target_view()
                progress_dialog.destroy()

    def on_fsetsInfo_activate(self, widget):
        fsetInfoDialog = DisplayFsetInfo(self.sdk)
        fsetInfoDialog.run()

    def on_editRepo_activate(self, widget):
        dialog_tree = gtk.glade.XML(self.gladefile, 'fsetsInfo')
        dialog = dialog_tree.get_widget('fsetsInfo')
        dialog.set_title(_("Choose a Platform"))

        platformComboBox = dialog_tree.get_widget('platform')
        cell = gtk.CellRendererText()
        platformComboBox.pack_start(cell, True)
        platformComboBox.add_attribute(cell, 'text', 0)

        platformList = sorted(self.sdk.platforms.iterkeys())
        platformEntryList = gtk.ListStore(gobject.TYPE_STRING)
        for pname in platformList:
            platformEntryList.append([pname])
        platformComboBox.set_model(platformEntryList)

        infoText = dialog_tree.get_widget('info')
        infoText.hide()
        fsetComboBox = dialog_tree.get_widget('fset')
        fsetComboBox.hide()

        dialog.run()
        dialog.destroy()

        platformName = platformComboBox.get_active_text()
        if platformName:            
            if self.sdk.platforms[platformName].config_info['package_manager'] == 'yum':
                editRepo = repo_editor.repoEditor(self.sdk, os.path.join(self.sdk.platforms[platformName].path, "yum.repos.d"))
                editRepo.run()
            else:
                self.show_error_dialog(_("This feature is currently available for Yum based platforms only"))

    def on_cmd_history_clicked(self, widget):
        cmd_dlg = CommandHistoryDlg(self.sdk, self.cmd_history)
        is_clean = cmd_dlg.run()
        if is_clean == True:
            self.clean_cmd_list()

    def append_cmd_list(self, cmd):
        if len (self.cmd_history) == 0:
            self.buttons.extract_cmds.set_sensitive(True)
        self.cmd_history.append(cmd)

    def clean_cmd_list(self):
        self.cmd_history[:]=[]
        self.buttons.extract_cmds.set_sensitive(False)

class CommandHistoryDlg(object):
    """Class to bring up command history dialogue"""
    def __init__(self, sdk, cmd_history):
        self.cmd_history = cmd_history
        self.cmd_txt=""
        for item in self.cmd_history:
            self.cmd_txt = self.cmd_txt + item + '\n'
        self.sdk = sdk
        self.gladefile = os.path.join(self.sdk.path, "image-creator.glade")
        self.widgets = gtk.glade.XML (self.gladefile, 'cmd_history_dlg')
        dic = { "on_clean_btn_clicked" : self.on_clean_btn_clicked,
                "on_copy_btn_clicked" : self.on_copy_btn_clicked,
                "on_save_btn_clicked" : self.on_save_btn_clicked                }
        self.widgets.signal_autoconnect(dic)
        self.dialog = self.widgets.get_widget('cmd_history_dlg')
        self.is_clean = False

    def run(self):
        cmd_txtview = self.widgets.get_widget('cmd_text')
        cmd_txtbuff = cmd_txtview.get_buffer()
        cmd_txtbuff.set_text(self.cmd_txt)
        while True:
          if self.dialog.run() == gtk.RESPONSE_CLOSE:
            break
        self.dialog.destroy()
        return self.is_clean

    def on_clean_btn_clicked(self, widget):
        cmd_txtview = self.widgets.get_widget('cmd_text')
        cmd_txtbuff = cmd_txtview.get_buffer()
        cmd_txtbuff.set_text('')
        self.cmd_history[:] = []
        self.cmd_txt=''
        self.is_clean = True
        
    def on_copy_btn_clicked(self, widget):
        clipboard = gtk.clipboard_get()
        clipboard.set_text(self.cmd_txt)
        clipboard.store()

    def on_save_btn_clicked(self, widget):
        cmds_path = paths.LOCALSTATEDIR + '/lib/moblin-image-creator/cmds'
        while True:
            widgets = gtk.glade.XML(self.gladefile, 'save_dlg')
            dialog = widgets.get_widget('save_dlg')
            dialog.set_default_response(gtk.RESPONSE_OK)
            widgets.get_widget('file_name').set_text('.mic')
            result = dialog.run()
            file_name = widgets.get_widget('file_name').get_text()
            dialog.destroy()
            if result != gtk.RESPONSE_OK:
                break
            if file_name and file_name != ".mic":
                if os.path.exists(cmds_path + '/' + file_name) == True:
                    widgets_exist = gtk.glade.XML(self.gladefile, 'file_exist')
                    dlg_exist = widgets_exist.get_widget('file_exist')
                    dlg_exist.set_default_response(gtk.RESPONSE_CANCEL)
                    result_exist = dlg_exist.run()
                    dlg_exist.destroy()
                    if result_exist == gtk.RESPONSE_OK:
                        break
                else:
                    break

        if os.path.exists (cmds_path) == False:
            print _("Creating folder %s ... ") % cmds_path
            cmd = 'mkdir ' + cmds_path
            os.popen(cmd)
        
        mic_file = open(cmds_path + '/' + file_name, 'w')
        print >> mic_file, "%s" % self.cmd_txt
        mic_file.close()
     
        return

#Class: Display Fset Info
class DisplayFsetInfo(object):
    def __init__(self, sdk):
        self.sdk = sdk
        self.gladefile = os.path.join(self.sdk.path, "image-creator.glade")
        dialog_tree = gtk.glade.XML(self.gladefile, 'fsetsInfo')
        self.dialog = dialog_tree.get_widget('fsetsInfo')

        infoText = dialog_tree.get_widget('info')
        self.textBuffer = gtk.TextBuffer()
        self.textBuffer.set_text(_("Please Select a Platform"))
        infoText.set_buffer(self.textBuffer)
        infoText.set_editable(False)

        self.platformComboBox = dialog_tree.get_widget('platform')
        cell = gtk.CellRendererText()
        self.platformComboBox.pack_start(cell, True)
        self.platformComboBox.add_attribute(cell, 'text', 0)
        self.platformComboBox.connect('changed', self.platformChanged)

        self.fsetComboBox = dialog_tree.get_widget('fset')
        cell2 = gtk.CellRendererText()
        self.fsetComboBox.pack_start(cell2, True)
        self.fsetComboBox.add_attribute(cell2, 'text', 0)
        self.fsetComboBox.connect('changed', self.fsetChanged)

        self.fsetEntryList = gtk.ListStore(gobject.TYPE_STRING)
        self.fsetComboBox.set_model(self.fsetEntryList)


        platformList = sorted(self.sdk.platforms.iterkeys())
        platformEntryList = gtk.ListStore(gobject.TYPE_STRING)
        for pname in platformList:
            platformEntryList.append([pname])
        self.platformComboBox.set_model(platformEntryList)

        width, height = self.dialog.get_default_size()
        self.dialog.set_default_size(width + 500, height + 250)

    def fsetChanged(self, widget):
        platformName = self.platformComboBox.get_active_text()
        platform = self.sdk.platforms[platformName]
        fsetName = self.fsetComboBox.get_active_text()        
        if fsetName == None:
            return
        self.textBuffer.set_text(_("Fset Description: %s") % platform.fset[fsetName].desc)
        #self.textBuffer.insert_at_cursor(_("\nFset Dedendency: %s") % platform.fset[fsetName].deps)
        self.textBuffer.insert_at_cursor(_("\n\nFset Dedendency: "))
        for depends in sorted(platform.fset[fsetName].deps):
            self.textBuffer.insert_at_cursor(" %s " % depends)
        self.textBuffer.insert_at_cursor(_("\n\nPackages in the Fset: "))
        i = 0
        for packages in sorted(platform.fset[fsetName].pkgs):
            self.textBuffer.insert_at_cursor(" %s " % packages)
            i += 1
            if i > 5:
                i = 0
                self.textBuffer.insert_at_cursor("\n                       ")
        self.textBuffer.insert_at_cursor(_("\n\nDebug Packages in the Fset: "))
        for packages in sorted(platform.fset[fsetName].debug_pkgs):
            self.textBuffer.insert_at_cursor(" %s " % packages)        
        

    def platformChanged(self, widget):
        self.textBuffer.set_text(_("Please Select an Fset"))
        self.fsetEntryList.clear()
        platformName = self.platformComboBox.get_active_text()
        platform = self.sdk.platforms[platformName]
        all_fsets = set(platform.fset)
        for fset_name in sorted(all_fsets):
            self.fsetEntryList.append([fset_name])

    def run(self):
        self.dialog.run()
        self.dialog.destroy()


#Class: Adding a New Project
class AddNewProject(object):
    """Class to bring up AddNewProject dialogue"""
    def __init__(self, sdk, gladefile, name="", desc="", path="", platform="", dialogName=""):
        packageManager = ""
        if mic_cfg.config.has_option('general', 'package_manager'):
            packageManager = mic_cfg.config.get('general', 'package_manager')
        self.sdk = sdk
        if dialogName:
            widgets = gtk.glade.XML (gladefile, dialogName)
        else:
            widgets = gtk.glade.XML (gladefile, 'newProject')
        widgets.signal_autoconnect({"on_browse": self.on_browse})
        if dialogName:
            self.dialog = widgets.get_widget(dialogName)
        else:
            self.dialog = widgets.get_widget('newProject')
        self.np_name = widgets.get_widget("np_name")
        self.np_name.set_text(name)
        self.np_desc = widgets.get_widget("np_desc")
        self.np_desc.set_text(desc)
        self.np_path = widgets.get_widget("np_path")
        self.np_path.set_text(path)
        self.np_platform = widgets.get_widget("np_platform")
        self.np_platform.connect("changed", self.platform_callback)
        self.np_platform_desc_text = gtk.TextBuffer()
        self.np_platform_desc = widgets.get_widget("np_platform_desc")
        self.np_platform_desc.set_buffer(self.np_platform_desc_text)
        if not dialogName:
            self.np_addTarget = widgets.get_widget("np_addTarget")
            self.np_targetName_label = widgets.get_widget("np_targetName_label")
            self.np_addTarget.connect("clicked", self.addTarget_callback)
            self.target_name = None
        platform_entry_box = gtk.ListStore(gobject.TYPE_STRING)
        platforms = sorted(self.sdk.platforms.iterkeys())
        platform_idx = 0
        idx = 0
        for pname in platforms:
            pdesc = ""
            added = False
            packageManagerDesc = ""
            if self.sdk.platforms[pname].config_info != None:
                pdesc = " - (%s)" % self.sdk.platforms[pname].config_info['description']
                packageManagerDesc = self.sdk.platforms[pname].config_info['package_manager']
            #if packageManager == packageManagerDesc:
                #platform_entry_box.append([pname + pdesc])
            platform_entry_box.append([pname])
            added = True
            #elif packageManagerDesc == "":
                #platform_entry_box.append([pname + pdesc])
            #    platform_entry_box.append([pname])
            #    added = True
            # If previously selected an entry, select it again
            if added:
                if  (pname + pdesc) == platform:
                    platform_idx = idx
                idx += 1
        self.np_platform.set_model(platform_entry_box)
        self.np_platform.set_active(platform_idx)
        width, height = self.dialog.get_default_size()
        self.dialog.set_default_size(width + 500, height)

    def platform_callback(self, widget):
        pname = self.np_platform.get_active_text().split()[0]
        self.np_platform_desc_text.set_text(self.sdk.platforms[pname].config_info['description'])

    def addTarget_callback(self, widget):
        while True:
            gladefile = os.path.join(self.sdk.path, "image-creator.glade")
            widgets = gtk.glade.XML(gladefile, 'nt_dlg')
            dialog = widgets.get_widget('nt_dlg')
            dialog.set_default_response(gtk.RESPONSE_OK)
            result = dialog.run()
            target_name = widgets.get_widget('nt_name').get_text()
            target_name = target_name.strip()
            dialog.destroy()
            if result == gtk.RESPONSE_OK:
                if not target_name:
                    widgets = gtk.glade.XML(gladefile, 'error_dialog')
                    widgets.get_widget('error_label').set_text(_("Must specify a target name"))
                    dialog = widgets.get_widget('error_dialog')
                    dialog.run()
                    dialog.destroy()
                else:
                    self.target_name = target_name
                    self.np_targetName_label.set_text(_("Adding Target: %s") % self.target_name)
                    break
            else:
                break


    def run(self):
        result = self.dialog.run()
        self.name = self.np_name.get_text()
        self.desc = self.np_desc.get_text()
        self.path = self.np_path.get_text()
        self.platform = self.np_platform.get_active_text()
        self.dialog.destroy()
        return result

    def on_browse(self, button):
        dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, title=_("Choose Project Directory"))
        dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        if dialog.run() == gtk.RESPONSE_OK:
            self.np_path.set_text(dialog.get_current_folder())
        dialog.destroy()

class MainWindowButtons(object):
    def __init__(self, widgets):
        # Project button bar
        self.add_project = widgets.get_widget('new_project_add')
        self.delete_project = widgets.get_widget('project_delete')
        self.upgrade_project = widgets.get_widget('upgrade_project')
        self.extract_cmds = widgets.get_widget('cmd_history')
        # Target button bar
        self.add_target = widgets.get_widget('new_target_add')
        self.delete_target = widgets.get_widget('target_delete')
        self.install_fset = widgets.get_widget('target_install_fset')
        self.install_group = widgets.get_widget('target_install_group')
        self.upgrade_target = widgets.get_widget('upgrade_target')
        self.edit_repo = widgets.get_widget('edit_repo')
        # Action buttons
        self.create_liveusb = widgets.get_widget('create_liveUSB_btn')
        self.create_liverwusb = widgets.get_widget('create_liveRWUSB_btn')
        self.create_nfsliveusb = widgets.get_widget('create_NFSliveUSB_btn')
        self.create_installusb = widgets.get_widget('create_installUSB_btn')
        self.create_liveCD = widgets.get_widget('create_liveCD_btn')
        self.create_nfsliveCD = widgets.get_widget('create_NFSliveCD_btn')
        self.create_installCD = widgets.get_widget('create_installCD_btn')
        self.create_NAND = widgets.get_widget('create_NAND_btn')
        # Terminal button
        self.term_launch = widgets.get_widget('term_launch')
        self.target_term_launch = widgets.get_widget('target_term_launch')
        self.target_config = widgets.get_widget('target_config')
        self.Write_USB = widgets.get_widget('Write_USB')
        self.create_launchvm = widgets.get_widget('launch_vm_btn')

def print_exc_plus():
    # From Python Cookbook 2nd Edition.  FIXME: Will need to remove this at
    # some point, or give attribution.
    """ Print the usual traceback information, followed by a listing of
        all the local variables in each frame.
    """
    tb = sys.exc_info()[2]
    while tb.tb_next:
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    traceback.print_exc()
    print _("Locals by frame, innermost last")
    for frame in stack:
        print
        print _("Frame %s in %s at line %s") % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            print _("\t%20s = ") % key,
            # we must _absolutely_ avoid propagating exceptions, and str(value)
            # COULD cause any exception, so we MUST catch any...:
            try:
                print value
            except:
                print _("<ERROR WHILE PRINTING VALUE>")
    traceback.print_exc()

if __name__ == '__main__':
    app = App()
    app.run()
