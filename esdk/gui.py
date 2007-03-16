#!/usr/bin/env python

import pygtk
import gtk, gtk.glade, gobject
from SDK import *


class esdkMain:
	"""
	This is our main
	"""
	def __init__(self):
		gladefile = "/usr/share/esdk/esdk.glade"
		self.widgets = gtk.glade.XML (gladefile, 'main')
		
		#self.widgets.signal_autoconnect(callbacks.__dict__)
		dic = {"on_main_destroy_event" : gtk.main_quit,
			"on_quit_activate" : gtk.main_quit,
			"on_newProject_clicked" : self.on_newProject_clicked,
			"on_projectDelete_clicked": self.on_projectDelete_clicked,
			"on_projectSave_clicked": self.on_projectSave_clicked,
			"on_about_activate": self.on_about_activate}
		self.widgets.signal_autoconnect(dic)
		
		#setup projectList widget
		self.pName = "Name"
		self.pDesc = "Description"
		self.pPath = "Path"
		self.pPlatform = "Platform"

		self.projectList = self.widgets.get_widget("projectList")
		print "Setting Project List"
		self.set_plist(self.pName, 0)
		self.set_plist(self.pDesc, 1)
		self.set_plist(self.pPath, 2)
		self.set_plist(self.pPlatform, 3)

		self.projectView = gtk.ListStore(str, str, str, str)
		self.projectList.set_model(self.projectView)
		self.projectList.set_reorderable(1)

		#Set targetList widget
		self.tParent = "Parent"
		self.tName = "Name"

		self.targetList = self.widgets.get_widget("targetList")
		print "Setting Target List"
		self.set_tlist(self.tParent, 0)
		self.set_tlist(self.tName, 1)

		self.targetView = gtk.ListStore(str, str)
		self.targetList.set_model(self.targetView)
		
		
		#read in project list using SDK()
		#FIXME: I'm only reading them, not saving a handle to each
		sdk = SDK()
		for key in sdk.projects.keys():
			my_project = ProjectInfo()
			saved_projects = sdk.projects[key]
			print 'Found: name: %s ' % (saved_projects.name)
			my_project.name = '%s' % saved_projects.name
			my_project.path = '%s' % saved_projects.path
			#my_project.desc = saved_projects.desc
			my_project.platform = '%s' % saved_projects.platform.name
			self.projectView.append(my_project.getList())

			#get Targets related to each project
			print "Targets for project: %s" % saved_projects.name
			for t in saved_projects.targets.keys():
				my_targets = saved_projects.targets[t]
				print "\t%s" % my_targets.name

		self.selection = self.projectList.get_selection()
		model, iter = self.selection.get_selected()
		self.selection.connect("changed", self.display_selected)

	def display_selected(model, iter):
		print "user selected something else "

	"""Add project list column descriptions"""
	def set_plist(self, name, id):
		column = gtk.TreeViewColumn(name, gtk.CellRendererText()
			, text=id)	
		column.set_resizable(True)		
		column.set_sort_column_id(id)
		self.projectList.append_column(column)

	"""Add target list column descriptions"""
	def set_tlist(self, name, id):
		column = gtk.TreeViewColumn(name, gtk.CellRendererText()
			, text=id)	
		column.set_resizable(True)		
		column.set_sort_column_id(id)
		self.targetList.append_column(column)

	def on_newProject_clicked(self, widget):
		print "New project Dialogue"
		"""Instantiate a new dialogue"""
		new_project = AddNewProject();
		"""Now call its run method"""
		result,new_project = AddNewProject.run(new_project)
		if (result == gtk.RESPONSE_OK):
			"""The user clicked Ok, so let's add this
			project to the projectList list"""
			print "user pressed OK"
			sdk = SDK()
			platform = sdk.platforms[new_project.platform]
			print "platform %s "  % platform.name
			proj = sdk.create_project(new_project.path, new_project.name, new_project.desc, platform)
			#FIXME: finish packing this dialogue
			if (proj):
				print "Project create OK"
				dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
				dialog.set_title("Project Creation Succeeded")
				dialog.set_size_request(200, 200)
				dialog.connect("delete_event", self.dialog.destroy)
				vbox = gtk.VBox()
				vbox.pack_start("Project Created Successfully")
				dialog.add(self.vbox)

				dialog.show_all()
			#FIXME: error check
			self.projectView.append(new_project.getList())

	def on_about_activate(self, event):
		gtk.AboutDialog()
	def on_projectSave_clicked(self, event):
		print "Not yet implemented"
	def on_projectDelete_clicked(self, event):
		print "Not yet implemented"
		

class TargetInfo:
	"""Class defining target elements"""
	def __init__(self, path="", fsets=""):
		self.parent = parent
		self.name = name
	def getTargetList(self):
		return [self.parent, self.name]
class ProjectInfo:
	"""Class to store new project info before we persisit"""
	def __init__(self, name="", desc="", path="", platform=""):
		self.name = name
		self.desc = desc
		self.path = path
		self.platform = platform
	def getList(self):
		return [self.name, self.desc, self.path, self.platform]

class AddNewProject:
	"""Class to bring up AddNewProject dialogue"""
	def __init__(self, name="", desc="", path="", platform=""):
		self.gladefile = "esdk.glade"
		self.newProject = ProjectInfo(name,desc,path,platform)
	def on_newDlg_destroy(event):
		print "Destroying dialogue"
		gtk.newProject.destroy()
	def on_newDlg_cancel_clicked(event):
		print "dialogue closing"
	def run(self):
		self.widgets = gtk.glade.XML (self.gladefile, 'newProject')
		self.newDlg = self.widgets.get_widget('newProject')
		
		#Get all of the Entry Widgets and set their text
		self.np_name = self.widgets.get_widget("np_name")
		self.np_name.set_text(self.newProject.name)
		self.np_desc = self.widgets.get_widget("np_desc")
		self.np_desc.set_text(self.newProject.desc)
		self.np_path = self.widgets.get_widget("np_path")
		self.np_path.set_text(self.newProject.path)
		self.np_platform = self.widgets.get_widget("np_platform")
		self.np_platform.child.set_text(self.newProject.platform)

		store = gtk.ListStore(gobject.TYPE_STRING)
		for pname in SDK().platforms.keys():
			store.append([pname])
			
		self.np_platform.set_model(store)
		self.np_platform.set_text_column(0)
		
		self.result = self.newDlg.run()

		#get the values
		self.newProject.name = self.np_name.get_text()
		self.newProject.desc = self.np_desc.get_text()
		self.newProject.path = self.np_path.get_text()
		self.newProject.platform = self.np_platform.child.get_text()

		if (self.result == gtk.RESPONSE_CANCEL):
			print "User cancelled New project Add"
			self.newDlg.destroy()

		self.newDlg.destroy()

		return self.result,self.newProject
			
if __name__ == '__main__':
	esdk = esdkMain()
	gtk.main()

