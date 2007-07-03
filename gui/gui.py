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
import gtk.glade
import locale
import os
import pygtk
import shutil
import sys
import time
import traceback

import pdk_utils
import SDK 

# Initial stuff for Internationlization and Localization support.
# Locale stuff
# Set the locale to the user's preferred locale
locale.setlocale(locale.LC_ALL, '')
USER_LOCALE = locale.getlocale(locale.LC_ALL)

# More info: http://docs.python.org/lib/i18n.html
gettext.bindtextdomain('pdk', '/usr/share/pdk/locale')
gettext.textdomain('pdk')
gettext.install('pdk', '/usr/share/pdk/locale')
_ = gettext.lgettext

class App(object):
    """This is our main"""
    def __init__(self):

        self.sdk = SDK.SDK(cb = self)
        self.gladefile = os.path.join(self.sdk.path, "project-builder.glade")
        if not os.path.isfile(self.gladefile):
            raise IOError, "Glade file is missing from: %s" % self.gladefile
        gnome.init('project-builder', self.sdk.version, properties = {'app-datadir':self.sdk.path})
        self.widgets = gtk.glade.XML (self.gladefile, 'main')
        dic = {"on_main_destroy_event" : gtk.main_quit,
                "on_quit_activate" : gtk.main_quit,
                "on_help_activate" : self.on_help_activate,
                "on_new_project_clicked" : self.on_new_project_clicked,
                "on_projectDelete_clicked": self.on_projectDelete_clicked,
                "on_new_target_add_clicked": self.on_new_target_add_clicked,
                "on_delete_target_clicked": self.on_delete_target_clicked,
                "on_install_fset": self.on_install_fset,
                "on_create_liveISO_clicked": self.on_liveISO_clicked,
                "on_create_installISO_clicked": self.on_installISO_clicked,
                "on_create_liveUSB_clicked": self.on_liveUSB_clicked,
                "on_create_liveRWUSB_clicked": self.on_liveRWUSB_clicked,
                "on_create_installUSB_clicked": self.on_installUSB_clicked,
                "on_about_activate": self.on_about_activate,
                "on_term_launch_clicked": self.on_term_launch_clicked,
                "on_target_term_launch_clicked": self.on_target_term_launch_clicked,
                "on_target_kernel_cmdline_clicked": self.on_target_kernel_cmdline_clicked,
                "on_DD_USB_clicked": self.on_DD_USB_clicked}
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
        self.projectView.set_model(self.projectList)
#        self.projectView.set_reorderable(1)
        # Set targetView widget
        self.tName = _("Name")
        self.tFSet = _("Function Sets")
        self.targetView = self.widgets.get_widget("targetView")
        self.set_tlist(self.tName, 0)
        self.set_tlist(self.tFSet, 1)
        self.targetList = gtk.ListStore(str, str)
        self.targetView.set_model(self.targetList)
        # read in project list using SDK()
        for key in sorted(self.sdk.projects.iterkeys()):
            p = self.sdk.projects[key]
            self.projectList.append((p.name, p.desc, p.path, p.platform.name))
        self.buttons = MainWindowButtons(self.widgets)
        # Connect project selection signal to list targets in the targetList
        # widget: targetView
        self.projectView.get_selection().connect("changed", self.project_view_changed)
        self.targetView.get_selection().connect("changed", self.target_view_changed)

    def run(self):
        gtk.main()
        
    def on_help_activate(self, widget):
        gnome.help_display('project-builder')

    def target_view_changed(self, selection):
        model, iter = self.targetView.get_selection().get_selected()
        target_selected_state = False
        fset_state = False
        if iter:
            # A target is selected
            target_selected_state = True
            target = self.current_target()
            fsets = target.installed_fsets()
            if fsets:
                # We have fsets installed in the target
                fset_state = True
        # Items which should be enabled if we have a target selected
        self.buttons.delete_target.set_sensitive(target_selected_state)
        self.buttons.install_fset.set_sensitive(target_selected_state)
        # Items which should be enabled if our selected target has an fset
        self.buttons.create_liveiso.set_sensitive(fset_state)
        self.buttons.create_installiso.set_sensitive(fset_state)
        self.buttons.create_liveusb.set_sensitive(fset_state)
        self.buttons.create_liverwusb.set_sensitive(fset_state)
        self.buttons.create_installusb.set_sensitive(fset_state)
        self.buttons.target_term_launch.set_sensitive(fset_state)
        self.buttons.target_kernel_cmdline.set_sensitive(fset_state)
        self.buttons.DD_USB.set_sensitive(fset_state)

    def project_view_changed(self, selection):
        try:
            self.current_project().mount()
        except:
            pass
        self.redraw_target_view()

    def redraw_target_view(self):
        self.targetList.clear()
        model, iter = self.projectView.get_selection().get_selected()
        if not iter:
            # No projects are selected
            self.buttons.delete_project.set_sensitive(False)
            self.buttons.add_target.set_sensitive(False)
            self.buttons.install_fset.set_sensitive(False)
            self.buttons.delete_target.set_sensitive(False)
            self.buttons.term_launch.set_sensitive(False)
            return
        # We have a project selected, so it makes sense for the delete project
        # and add target buttons to be sensitive
        self.buttons.delete_project.set_sensitive(True)
        self.buttons.add_target.set_sensitive(True)
        self.buttons.term_launch.set_sensitive(True)
        for key in self.current_project().targets:
            installed_fsets = ' '.join(self.current_project().targets[key].installed_fsets())
            self.targetList.append((key, installed_fsets))

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

    def on_new_project_clicked(self, widget):
        """Instantiate a new dialogue"""
        name = ""
        desc = ""
        platform = ""
        path = ""
        while True:
            dialog = AddNewProject(sdk = self.sdk, name = name, gladefile = self.gladefile, desc = desc, platform = platform, path = path)
            result = dialog.run()
            if result != gtk.RESPONSE_OK:
                break
            if not dialog.name or not dialog.desc or not dialog.platform or not dialog.path:
                self.show_error_dialog("All values must be specified")
            else:
                break
            name = dialog.name
            desc = dialog.desc
            platform = dialog.platform
            path = dialog.path
        if result == gtk.RESPONSE_OK:
            try:
                progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                progress_dialog = progress_tree.get_widget('ProgressDialog')
                progress_dialog.connect('delete_event', self.ignore)
                progress_tree.get_widget('progress_label').set_text(_("Please wait while installing %s") % dialog.name)
                self.progressbar = progress_tree.get_widget('progressbar')
                proj = self.sdk.create_project(dialog.path, dialog.name, dialog.desc, self.sdk.platforms[dialog.platform]).install()
                self.projectList.append((dialog.name, dialog.desc, dialog.path, dialog.platform))
            except:
                print sys.exc_value
                self.show_error_dialog("%s" % (sys.exc_value))
                try:
                    self.sdk.delete_project(dialog.name)
                except:
                    # if the project creation failed before the list of
                    # projects has been updated, then we expect failure here
                    pass
            progress_dialog.destroy()

    def on_about_activate(self, event):
        dialog = gtk.AboutDialog()
        dialog.set_name('Project Builder')
        dialog.set_version(self.sdk.version)
        dialog.set_comments(_("A tool for building Mobile and/or Single Purposed Linux Device Stacks"))
        try:
            f = open(os.path.join(self.sdk.path, "COPYING"), "r")
            dialog.set_license(f.read())
            f.close()
        except:
            print >> sys.stderr, sys.exc_value
            pass
        dialog.set_copyright("Copyright Intel Corp. 2007")
        dialog.set_website('http://ADDMYURLHERE')
        dialog.set_website_label('Project Development Kit Home')
        dialog.run()
        dialog.destroy()

    def on_projectDelete_clicked(self, event):
        """Delete a Project"""
        project = self.current_project()
        tree = gtk.glade.XML(self.gladefile, 'qDialog')
        tree.get_widget('queryLabel').set_text("Delete the %s project?" % (project.name))
        dialog = tree.get_widget('qDialog')
        result = dialog.run()
        dialog.destroy()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text(_("Please wait while deleting %s") % project.name)
            self.progressbar = progress_tree.get_widget('progressbar')
            self.sdk.delete_project(project.name)
            self.remove_current_project()
            progress_dialog.destroy()
            
    def on_new_target_add_clicked(self, widget):
        # Open the "New Target" dialog
        while True:
            widgets = gtk.glade.XML(self.gladefile, 'nt_dlg')
            dialog = widgets.get_widget('nt_dlg')
            dialog.set_default_response(gtk.RESPONSE_OK)
            result = dialog.run()
            target_name = widgets.get_widget('nt_name').get_text()
            target_name = target_name.strip()
            dialog.destroy()
            if result == gtk.RESPONSE_OK:
                if not target_name:
                    self.show_error_dialog("Must specify a target name")
                else:
                    progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
                    progress_dialog = progress_tree.get_widget('ProgressDialog')
                    progress_dialog.connect('delete_event', self.ignore)
                    progress_tree.get_widget('progress_label').set_text(_("Please wait while creating %s") % target_name)
                    self.progressbar = progress_tree.get_widget('progressbar')
                    self.current_project().create_target(target_name)
                    self.targetList.append((target_name, ''))
                    progress_dialog.destroy()
                    break
            else:
                break

    def on_install_fset(self, widget):
        tree = gtk.glade.XML(self.gladefile, 'installFsetDialog')
        dialog = tree.get_widget('installFsetDialog')
        platform = self.current_project().platform
        label = tree.get_widget('fset-desc-label')
        checkbox = tree.get_widget('debug-check-button')
        list = gtk.ListStore(gobject.TYPE_STRING)
        iter = 0
        all_fsets = set(platform.fset)
        installed_fsets = set(self.current_target().installed_fsets())
        for fset_name in sorted(all_fsets.difference(installed_fsets)):
            iter = list.append([fset_name])
        if not iter:
            self.show_error_dialog("Nothing available to install!")
            dialog.destroy()
            return
        cebox = tree.get_widget('installed_fsets')
 
        cebox.set_model(list)
        cebox.set_active(0)
        cebox.connect("changed", self.fset_install_updated, label, platform, checkbox)
        label.set_text(platform.fset[cebox.get_active_text()].desc)
        checkbox.set_sensitive(True)
        if dialog.run() == gtk.RESPONSE_OK:
            fset = platform.fset[cebox.get_active_text()]
            debug = checkbox.get_active()
            dialog.destroy()
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            self.progressbar = progress_tree.get_widget('progressbar')
            progress_tree.get_widget('progress_label').set_text("Please wait while installing %s" % fset.name)
            try:
                self.current_target().installFset(fset, fsets = platform.fset, debug = debug)
                self.redraw_target_view()
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                print_exc_plus()
                self.show_error_dialog("Unexpected error: %s" % (sys.exc_info()[1]))
            progress_dialog.destroy()
        dialog.destroy();

    def ignore(self, *args):
        return True
    
    def iteration(self, process):
        self.progressbar.pulse()
        gtk.main_iteration()
        time.sleep(0.01)
            
    def fset_install_updated(self, box, label, platform, checkbox):
        fset = platform.fset[box.get_active_text()]
        checkbox.set_sensitive(True)
        label.set_text(fset.desc)

    def on_delete_target_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        tree = gtk.glade.XML(self.gladefile, 'qDialog')
        tree.get_widget('queryLabel').set_text("Delete target %s from project %s?" % (target.name, project.name))
        dialog = tree.get_widget('qDialog')
        if dialog.run() == gtk.RESPONSE_OK:
            self.sdk.projects[project.name].delete_target(target.name)
            self.remove_current_target()
        dialog.destroy()

    def current_project(self):
        model, iter = self.projectView.get_selection().get_selected()
        return self.sdk.projects[model[iter][0]]

    def current_target(self):
        model, iter = self.targetView.get_selection().get_selected()
        return self.current_project().targets[model[iter][0]]

    def remove_current_project(self):
        model, iter = self.projectView.get_selection().get_selected()
        self.projectList.remove(iter)

    def remove_current_target(self):
        model, iter = self.targetView.get_selection().get_selected()
        self.targetList.remove(iter)

    def show_error_dialog(self, message="An unknown error has occurred!"):
        widgets = gtk.glade.XML(self.gladefile, 'error_dialog')
        widgets.get_widget('error_label').set_text(message)
        dialog = widgets.get_widget('error_dialog')
        dialog.run()
        dialog.destroy()

    def on_term_launch_clicked(self, widget):
        project_path = self.current_project().path
        print "Project path: %s" % project_path
        os.system('/usr/bin/gnome-terminal -x sudo /usr/sbin/chroot %s su - &' % project_path)

    def on_target_term_launch_clicked(self, widget):
        project_path = self.current_project().path
        target = self.current_target()
        target.mount()
        target_path= "%s/targets/%s/fs" % (project_path, target.name)
        print "Target path: %s" % target_path
        os.system('/usr/bin/gnome-terminal -x sudo /usr/sbin/chroot %s su - &' % target_path)

    def on_target_kernel_cmdline_clicked(self, widget):
        project_path = self.current_project().path
        target = self.current_target()
        target_path= "%s/targets/%s/image" % (project_path, target.name)
        widgets = gtk.glade.XML(self.gladefile, 'kernel_cmdline_dlg')
        dialog = widgets.get_widget('kernel_cmdline_dlg')
        usb_kernel_cmdline = widgets.get_widget('usb_kernel_cmdline')
        hd_kernel_cmdline = widgets.get_widget('hd_kernel_cmdline')
        usb_kernel_cmdline.set_text(self.current_project().get_target_usb_kernel_cmdline(target.name))
        hd_kernel_cmdline.set_text(self.current_project().get_target_hd_kernel_cmdline(target.name))
        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            self.current_project().set_target_usb_kernel_cmdline(target.name, usb_kernel_cmdline.get_text())
            self.current_project().set_target_hd_kernel_cmdline(target.name, hd_kernel_cmdline.get_text())
        dialog.destroy()

    def on_liveUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(self.gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        img_name = widgets.get_widget('img_name').get_text()
        dialog.destroy()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text("Please wait while while creating %s" % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                self.current_project().create_live_usb(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_liveRWUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(self.gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        img_name = widgets.get_widget('img_name').get_text()
        dialog.destroy()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text("Please wait while creating %s" % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                self.current_project().create_live_usb(target.name, img_name, 'EXT3FS')
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()
            progress_dialog.destroy()
            
    def on_installUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(self.gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        img_name = widgets.get_widget('img_name').get_text()
        dialog.destroy()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text("Please wait while creating %s" % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                self.current_project().create_install_usb(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()
            progress_dialog.destroy()

    def on_installISO_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(self.gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        img_name = widgets.get_widget('img_name').get_text()
        dialog.destroy()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text("Please wait while creating %s" % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                self.current_project().create_install_iso(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()
            progress_dialog.destroy()
            
    def on_liveISO_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(self.gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        img_name = widgets.get_widget('img_name').get_text()
        dialog.destroy()
        if result == gtk.RESPONSE_OK:
            progress_tree = gtk.glade.XML(self.gladefile, 'ProgressDialog')
            progress_dialog = progress_tree.get_widget('ProgressDialog')
            progress_dialog.connect('delete_event', self.ignore)
            progress_tree.get_widget('progress_label').set_text("Please wait while creating %s" % img_name)
            self.progressbar = progress_tree.get_widget('progressbar')
            try:
                self.current_project().create_live_iso(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()
            progress_dialog.destroy()
            
    def on_DD_USB_clicked(self, widget):
        project_path = self.current_project().path
        target = self.current_target()
        target_path= "%s/targets/%s/image" % (project_path, target.name)
        os.chdir(target_path)
        dialog = gtk.FileChooserDialog('Select Image File',None,gtk.FILE_CHOOSER_ACTION_OPEN,(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK),None)
        result = dialog.run()
        if result == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            print "No target image selected!"
        if result == gtk.RESPONSE_OK:
            targetfilename=dialog.get_filename()
            print "Selected file name: %s " % targetfilename
            dialog.destroy()
            widgets = gtk.glade.XML(self.gladefile, 'select_usb_disk_dialog')
            dialog2 = widgets.get_widget('select_usb_disk_dialog')
            usb_dev_list = gtk.ListStore(gobject.TYPE_STRING)
            usb_disk_list = pdk_utils.get_current_udisks()
            if not usb_disk_list:
                self.show_error_dialog('No USB disk detected! Please plug in your USB disk and try again!')
                dialog2.destroy()
                return -1
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
            if result == gtk.RESPONSE_CANCEL:
                print "No USB device selected!"
            if result == gtk.RESPONSE_OK:
                model, iter = usb_disks.get_selection().get_selected()
                if not iter:
                    self.show_error_dialog('No USB disk selected!')
                else:
                    print "Selected USB disk %s" % model[iter][0]
                    if not pdk_utils.umount_device(model[iter][0]):
                        self.show_error_dialog("Can not umount %s. Please close any shells or opened files still under mount point and try again!" % model[iter][0])
                        dialog2.destroy()
                        return -1
                    shutil.copyfile(targetfilename, model[iter][0])
            dialog2.destroy()

#Class: Adding a New Project
class AddNewProject(object):
    """Class to bring up AddNewProject dialogue"""
    def __init__(self, sdk, gladefile, name="", desc="", path="", platform=""):
        self.sdk = sdk
        widgets = gtk.glade.XML (gladefile, 'newProject')
        widgets.signal_autoconnect({"on_browse": self.on_browse})
        self.dialog = widgets.get_widget('newProject')
        self.np_name = widgets.get_widget("np_name")
        self.np_name.set_text(name)
        self.np_desc = widgets.get_widget("np_desc")
        self.np_desc.set_text(desc)
        self.np_path = widgets.get_widget("np_path")
        self.np_path.set_text(path)
        self.np_platform = widgets.get_widget("np_platform")
        platform_entry_box = gtk.ListStore(gobject.TYPE_STRING)
        for pname in sorted(self.sdk.platforms.iterkeys()):
            platform_entry_box.append([pname])
        self.np_platform.set_model(platform_entry_box)
        if platform:
            self.np_platform.child.set_text(platform)
        else:
            self.np_platform.set_active(0)

    def run(self):
        result = self.dialog.run()
        self.name = self.np_name.get_text()
        self.desc = self.np_desc.get_text()
        self.path = self.np_path.get_text()
        self.platform = self.np_platform.get_active_text()
        self.dialog.destroy()
        return result

    def on_browse(self, button):
        dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, title="Choose Project Directory")
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
        # Target button bar
        self.add_target = widgets.get_widget('new_target_add')
        self.delete_target = widgets.get_widget('target_delete')
        self.install_fset = widgets.get_widget('target_install_fset')
        # Action buttons
        self.create_liveiso = widgets.get_widget('create_liveISO_btn')
        self.create_installiso = widgets.get_widget('create_installISO_btn')
        self.create_liveusb = widgets.get_widget('create_liveUSB_btn')
        self.create_liverwusb = widgets.get_widget('create_liveRWUSB_btn')
        self.create_installusb = widgets.get_widget('create_installUSB_btn')
        # Terminal button
        self.term_launch = widgets.get_widget('term_launch')
        self.target_term_launch = widgets.get_widget('target_term_launch')
        self.target_kernel_cmdline = widgets.get_widget('target_kernel_cmdline')
        self.DD_USB = widgets.get_widget('DD_USB')
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
    print "Locals by frame, innermost last"
    for frame in stack:
        print
        print "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            print "\t%20s = " % key,
            # we must _absolutely_ avoid propagating exceptions, and str(value)
            # COULD cause any exception, so we MUST catch any...:
            try:
                print value
            except:
                print "<ERROR WHILE PRINTING VALUE>"
    traceback.print_exc()

if __name__ == '__main__':
    app = App()
    app.run()
