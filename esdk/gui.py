#!/usr/bin/python -tt
# vim: ai ts=4 sts=4 et sw=4

import pygtk
try:
    import gtk, gtk.glade, gobject
except:
    raise ImportError, "Unable to import the gtk libraries.  Maybe you are running in text mode"
from SDK import *
import os

global gladefile
gladefile = "/usr/share/esdk/esdk.glade"
if not os.path.isfile(gladefile):
    raise IOError, "Glade file is missing from: %s" % gladefile

class esdkMain:
    """This is our main"""
    def __init__(self):
        self.widgets = gtk.glade.XML (gladefile, 'main')
        dic = {"on_main_destroy_event" : gtk.main_quit,
                "on_quit_activate" : gtk.main_quit,
                "on_relnotes_activate" : self.on_relnotes_activate,
                "on_newProject_clicked" : self.on_newProject_clicked,
                "on_projectDelete_clicked": self.on_projectDelete_clicked,
                "on_new_target_add_clicked": self.on_new_target_add_clicked,
                "on_delete_target_clicked": self.on_delete_target_clicked,
                "on_install_fset": self.on_install_fset,
                "on_create_liveISO_clicked": self.on_liveISO_clicked,
                "on_create_installISO_clicked": self.on_installISO_clicked,
                "on_create_liveUSB_clicked": self.on_liveUSB_clicked,
                "on_create_installUSB_clicked": self.on_installUSB_clicked,
                "on_about_activate": self.on_about_activate,
                "on_term_launch_clicked": self.on_term_launch_clicked,
                "on_target_term_launch_clicked": self.on_target_term_launch_clicked}
        self.widgets.signal_autoconnect(dic)
        # setup projectView widget
        self.pName = "Name"
        self.pDesc = "Description"
        self.pPath = "Path"
        self.pPlatform = "Platform"
        self.projectView = self.widgets.get_widget("projectView")
        self.set_plist(self.pName, 0)
        self.set_plist(self.pDesc, 1)
        self.set_plist(self.pPath, 2)
        self.set_plist(self.pPlatform, 3)
        self.projectList = gtk.ListStore(str, str, str, str)
        self.projectView.set_model(self.projectList)
        self.projectView.set_reorderable(1)
        # Set targetView widget
        self.tName = "Name"
        self.tFSet = "Function Sets"
        self.targetView = self.widgets.get_widget("targetView")
        self.set_tlist(self.tName, 0)
        self.set_tlist(self.tFSet, 1)
        self.targetList = gtk.ListStore(str, str)
        self.targetView.set_model(self.targetList)
        # read in project list using SDK()
        for key in sorted(SDK().projects.iterkeys()):
            p = SDK().projects[key]
            self.projectList.append((p.name, p.desc, p.path, p.platform.name))
        self.buttons = MainWindowButtons(self.widgets)
        # Connect project selection signal to list targets in the targetList
        # widget: targetView
        self.projectView.get_selection().connect("changed", self.project_view_changed)
        self.targetView.get_selection().connect("changed", self.target_view_changed)
    
    def on_relnotes_activate(self, widget):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Project Builder Release Notes")
        window.set_resizable(True)
        window.set_default_size(400, 400)
        window.set_border_width(0)

        box1 = gtk.VBox(False, 0)
        window.add(box1)
        box1.show()

        box2 = gtk.VBox(False, 10)
        box1.pack_start(box2, True, True, 0)
        box2.show()

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textview = gtk.TextView()
        textbuffer = textview.get_buffer()
        scroll.add(textview)
        scroll.show()
        textview.show()

        box2.pack_start(scroll)

        rel_file = open("/usr/share/esdk/ReleaseNotes.txt", "r")

        if rel_file:
            txt = rel_file.read()
            rel_file.close()
            textbuffer.set_text(txt)
        window.show()

    def target_view_changed(self, selection):
        model, iter = self.targetView.get_selection().get_selected()
        if not iter:
            # No targets are selected
            self.buttons.delete_target.set_sensitive(False)
            self.buttons.install_fset.set_sensitive(False)
            self.buttons.target_term_launch.set_sensitive(False)
            return
        # A target has been selected
        self.buttons.delete_target.set_sensitive(True)
        self.buttons.install_fset.set_sensitive(True)
        self.buttons.create_liveiso.set_sensitive(True)
        self.buttons.create_installiso.set_sensitive(True)
        self.buttons.create_liveusb.set_sensitive(True)
        self.buttons.create_installusb.set_sensitive(True)
        self.buttons.target_term_launch.set_sensitive(True)
        
    def project_view_changed(self, selection):
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

    def on_newProject_clicked(self, widget):
        """Instantiate a new dialogue"""
        dialog = AddNewProject();
        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            sdk = SDK()
            sdk.create_project(dialog.path, dialog.name, dialog.desc, sdk.platforms[dialog.platform]).install()
            self.projectList.append((dialog.name, dialog.desc, dialog.path, dialog.platform))

    def on_about_activate(self, event):
        dialog = gtk.AboutDialog()
        dialog.set_name('Embedded Linux SDK: Project Builder')
        dialog.set_version('0.01 Pre-Alpha')
        dialog.set_comments('This is the graphical user front-end to the project-builder utility')
        dialog.set_license('TODO: Add License')
        dialog.set_website('http://umd.jf.intel.com')
        dialog.set_website_label('ESDK Developement')
        dialog.run()
        dialog.destroy()
        
    def on_projectDelete_clicked(self, event):
        """Delete a Project"""
        project = self.current_project()
        tree = gtk.glade.XML(gladefile, 'qDialog')
        tree.get_widget('queryLabel').set_text("Delete the %s project?" % (project.name))
        dialog = tree.get_widget('qDialog')
        if dialog.run() == gtk.RESPONSE_OK:
            SDK().delete_project(project.name)
            self.remove_current_project()
        dialog.destroy()

    def on_new_target_add_clicked(self, widget):
        # Open the "New Target" dialog
        widgets = gtk.glade.XML(gladefile, 'nt_dlg')
        dialog = widgets.get_widget('nt_dlg')
        if dialog.run() == gtk.RESPONSE_OK:
            target_name = widgets.get_widget('nt_name').get_text()
            self.current_project().create_target(target_name)
            self.targetList.append((target_name, ''))
        dialog.destroy()

    def on_install_fset(self, widget):
        tree = gtk.glade.XML(gladefile, 'installFsetDialog')
        dialog = tree.get_widget('installFsetDialog')
        platform = self.current_project().platform
        label = tree.get_widget('fset-desc-label')
        checkbox = tree.get_widget('debug-check-button')
        list = gtk.ListStore(gobject.TYPE_STRING)            
        for fset in self.current_project().platform.fset:
            list.append([fset])
        cebox = tree.get_widget('installed_fsets')
        cebox.set_model(list)
        cebox.set_text_column(0)
        cebox.child.set_text(list[0][0])
        cebox.connect("changed", self.fset_install_updated, label, platform, checkbox)
        label.set_text(platform.fset[cebox.child.get_text()].desc)
        if platform.fset[cebox.child.get_text()]['debug_pkgs']:
            checkbox.set_sensitive(True)
        else:
            checkbox.set_sensitive(False)
        if dialog.run() == gtk.RESPONSE_OK:
            fset = platform.fset[cebox.child.get_text()]
            try:
                self.current_target().install(fset, checkbox.get_active())
                self.redraw_target_view()
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()
        dialog.destroy()

    def fset_install_updated(self, box, label, platform, checkbox):
        fset = platform.fset[box.child.get_text()]
        if fset['debug_pkgs']:
            checkbox.set_sensitive(True)
        else:
            checkbox.set_sensitive(False)
        label.set_text(fset.desc)
        
    def on_delete_target_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        tree = gtk.glade.XML(gladefile, 'qDialog')
        tree.get_widget('queryLabel').set_text("Delete target %s from project %s?" % (target.name, project.name))
        dialog = tree.get_widget('qDialog')
        if dialog.run() == gtk.RESPONSE_OK:
            SDK().projects[project.name].delete_target(target.name)
            self.remove_current_target()
        dialog.destroy()

    def current_project(self):
        model, iter = self.projectView.get_selection().get_selected()
        return SDK().projects[model[iter][0]]

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
        widgets = gtk.glade.XML(gladefile, 'error_dialog')
        widgets.get_widget('error_label').set_text(message)
        dialog = widgets.get_widget('error_dialog')
        dialog.run()
        dialog.destroy()

    def on_term_launch_clicked(self, widget):
        project_path = self.current_project().path
        print "Project path: %s" % project_path
        os.system('/usr/bin/gnome-terminal -x sudo /usr/sbin/chroot %s &' % project_path)
   
    def on_target_term_launch_clicked(self, widget):
        project_path = self.current_project().path
        target = self.current_target()
        target_path= "%s/targets/%s/fs" % (project_path, target.name)
        print "Project path: %s" % target_path
        os.system('/usr/bin/gnome-terminal -x sudo /usr/sbin/chroot %s &' % target_path)

    def on_liveUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            try:
                img_name = widgets.get_widget('img_name').get_text()
                self.current_project().create_live_usb(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()                
        if result == gtk.RESPONSE_CANCEL:
            dialog.destroy()
        dialog.destroy()


    def on_installUSB_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            try:
                img_name = widgets.get_widget('img_name').get_text()
                self.current_project().create_install_usb(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()            
        if result == gtk.RESPONSE_CANCEL:
            dialog.destroy()
        dialog.destroy()


    def on_installISO_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        if result == gtk.RESPONSE_CANCEL:
            dialog.destroy()
        if result == gtk.RESPONSE_OK:
            try:
                img_name = widgets.get_widget('img_name').get_text()
                self.current_project().create_install_iso(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()                
        dialog.destroy()

    def on_liveISO_clicked(self, widget):
        project = self.current_project()
        target = self.current_target()
        widgets = gtk.glade.XML(gladefile, 'new_img_dlg')
        dialog = widgets.get_widget('new_img_dlg')
        result = dialog.run()
        if result == gtk.RESPONSE_CANCEL:
            dialog.destroy()
        if result == gtk.RESPONSE_OK:
            try:
                img_name = widgets.get_widget('img_name').get_text()
                self.current_project().create_live_iso(target.name, img_name)
            except ValueError, e:
                self.show_error_dialog(e.args[0])
            except:
                self.show_error_dialog()                
        dialog.destroy()


#Class: Adding a New Project
class AddNewProject:
    """Class to bring up AddNewProject dialogue"""
    def __init__(self, name="", desc="", path="", platform=""):
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
        for pname in sorted(SDK().platforms.iterkeys()):
            platform_entry_box.append([pname])
        self.np_platform.set_model(platform_entry_box)
        self.np_platform.set_text_column(0)
        if platform:
            self.np_platform.child.set_text(platform)
        else:
            self.np_platform.child.set_text(platform_entry_box[0][0])

    def run(self):
        result = self.dialog.run()
        self.name = self.np_name.get_text()
        self.desc = self.np_desc.get_text()
        self.path = self.np_path.get_text()
        self.platform = self.np_platform.child.get_text()
        self.dialog.destroy()
        return result

    def on_browse(self, button):
        dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, title="Choose Project Directory")
        dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        if dialog.run() == gtk.RESPONSE_OK:
            self.np_path.set_text(dialog.get_current_folder())
        dialog.destroy()
        
class MainWindowButtons:
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
        self.create_installusb = widgets.get_widget('create_installUSB_btn')
        # Terminal button
        self.term_launch = widgets.get_widget('term_launch')    
        self.target_term_launch = widgets.get_widget('target_term_launch')    
        
if __name__ == '__main__':
    esdk = esdkMain()
    gtk.main()
