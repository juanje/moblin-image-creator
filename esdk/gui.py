#!/usr/bin/env python

import pygtk
import gtk, gtk.glade
from SDK import *


class esdkMain:
	"""
	This is our main
	"""
	def __init__(self):
		gladefile = "esdk.glade"
		self.widgets = gtk.glade.XML (gladefile, 'main')
		#self.widgets.signal_autoconnect(callbacks.__dict__)
		dic = {"on_main_destroy_event" : gtk.main_quit,
			"on_quit_activate" : gtk.main_quit,
			"on_newProject_clicked" : self.on_newProject_clicked}
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
		
		#dummy project data for demonstration for example purpose
		#dummy_project = ProjectInfo()
		#dummy_project.name = "Test1"
		#dummy_project.desc = "iTest1"
		#dummy_project.path = "/home/user/something"
		#dummy_project.platform = "Donley"
		#self.projectView.append(dummy_project.getList())
		
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

		#Set targetList widget
		self.tPath = "Path"
		self.fsets = "Function Sets"

		self.targetList = self.widgets.get_widget("targetList")
		print "Setting Target List"
		self.set_tlist(self.tPath, 0)
		self.set_tlist(self.fsets, 1)

		self.targetView = gtk.ListStore(str, str)
		self.targetList.set_model(self.targetView)
		
		

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
			wine to the wine list"""
			print "user pressed OK"
			self.projectList.append(new_project.getList())
		if (result == get.RESPONSE_CANCEL):
			self.new_project.destroy()
class TargetInfo:
	"""Class defining target elements"""
	def __init__(self, path="", fsets=""):
		self.path = path
		self.fsets = fsets
	def getTargetList(self):
		return [self.path, self.fsets]
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
		self.np_platform.set_text(self.newProject.platform)	
		
		self.result = self.newDlg.run()

		return self.result
			
if __name__ == '__main__':
	esdk = esdkMain()
	gtk.main()

