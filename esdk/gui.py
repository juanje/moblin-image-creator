#!/usr/bin/python -tt

import pygtk
import gtk, gtk.glade, gobject
from SDK import *

global gladefile
gladefile = "/usr/share/esdk/esdk.glade"
if not os.path.isfile(gladefile):
	raise IOError, "Glade file is missing from: %s" % gladefile

class esdkMain:
	"""
	This is our main
	"""
	def __init__(self):
		self.widgets = gtk.glade.XML (gladefile, 'main')
		
		#self.widgets.signal_autoconnect(callbacks.__dict__)
		dic = {"on_main_destroy_event" : gtk.main_quit,
			"on_quit_activate" : gtk.main_quit,
			"on_newProject_clicked" : self.on_newProject_clicked,
			"on_projectDelete_clicked": self.on_projectDelete_clicked,
			"on_projectSave_clicked": self.on_projectSave_clicked,
			"on_new_target_add_clicked": self.on_new_target_add_clicked,
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
		self.tName = "Name"
		self.tFSet = "FSets"

		self.targetList = self.widgets.get_widget("targetList")
		print "Setting Target List"
		self.set_tlist(self.tName, 0)
		self.set_tlist(self.tFSet, 1)

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

		#Connect project selection signal to list targets
		#in the targetView widget: targetList
		self.selection = self.projectList.get_selection()
		model, iter = self.selection.get_selected()
		self.selection.connect("changed", self.get_proj_targets)

	#populate the Targets list based on user-selected Project
	""" Here we populate the targetList based on which
	projectView row the use selected
	"""
	def get_proj_targets(self, selection):
		
		#first clear whatever is already displayed
		self.targetView.clear()
		model, iter = selection.get_selected()
		projName = model[iter][0]
		print "User selected '%s' project, let's list the targets" % projName


		sdk = SDK()
		for key in sdk.projects.keys():
			projects = sdk.projects[key]
			if (projects.name == projName):
				print "Found project %s in main projects list" % projects.name
				print "Listing targets:"
				for t in projects.targets.keys():
					t_target = TargetInfo()
					my_target = projects.targets[t]
					print "\t%s" % my_target.name

					#ok let's add them to the widget targetView:targetList
					t_target.name = my_target.name
					t_target.fset = ''
					self.targetView.append(t_target.getList())




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
			#FIXME: error check
				self.projectView.append(new_project.getList())

	def on_about_activate(self, event):
		gtk.AboutDialog()
	def on_projectSave_clicked(self, event):
		print "Not yet implemented"

	#Delete a Project
	def on_projectDelete_clicked(self, event):
		selection = self.projectList.get_selection()

		model, iter = selection.get_selected()
		projectName = model[iter][0]
		print "Deleting project: %s" % projectName
		sdk = SDK()
		sdk.delete_project(projectName)
		iter = self.projectView.remove(iter)
				
	def on_new_target_add_clicked(self, widget):
		ntDlg = NewTarget();
		result, newTarget = ntDlg.run()
		
		name = newTarget.getList()
		new_name = name[0]
		if (result == gtk.RESPONSE_OK):
			print "new target: %s" % new_name
		#let's create it for the specific selected project
		selection = self.projectList.get_selection()

		model, iter = selection.get_selected()
		projectName = model[iter][0]
		print "Creating new target in project: %s" % projectName
		sdk = SDK()
		for key in sdk.projects.keys():
			project = sdk.projects[key]
			if (projectName == project.name):
				project.create_target(new_name)
		self.targetView.append(newTarget.getList())


		


class NewTargetInfo:
	def __init__(self, name="", fset=""):
		self.name = name
		self.fset = fset
	def getList(self):
		return [self.name, self.fset]

class NewTarget:
	"""Class to add a new selected project target"""
	def __init__(self, name=""):
		self.Target = NewTargetInfo(name)

	def run(self):
		"""Function to bring new project-target dialogue"""
		self.widget = gtk.glade.XML(gladefile, "nt_dlg")
		self.dlg = self.widget.get_widget("nt_dlg")

		self.t_name = self.widget.get_widget("nt_name")
		self.t_name.set_text(self.Target.name)

		self.result = self.dlg.run()

		self.Target.name = self.t_name.get_text()
		print "new target %s" % self.Target.name

		if (self.result == gtk.RESPONSE_CANCEL):
			print "User cancelled New project Add"
			self.dlg.destroy()

		self.dlg.destroy()

		return self.result, self.Target



class TargetInfo:
	"""Class defining target elements"""
	def __init__(self, name="", fset=""):
		self.name = name
		self.fset = fset
	def getList(self):
		return [self.name, self.fset]
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
		self.gladefile = '/usr/share/esdk/esdk.glade'
		self.newProject = ProjectInfo(name,desc,path,platform)
	def on_newDlg_destroy(event):
		print "Destroying dialogue"
		gtk.newProject.destroy()
	def on_newDlg_cancel_clicked(event):
		print "dialogue closing"
	def run(self):
		self.widgets = gtk.glade.XML (gladefile, 'newProject')
		self.newDlg = self.widgets.get_widget('newProject')
		
		#Get all of the Entry Widgets and set their text
		self.np_name = self.widgets.get_widget("np_name")
		self.np_name.set_text(self.newProject.name)
		self.np_desc = self.widgets.get_widget("np_desc")
		self.np_desc.set_text(self.newProject.desc)
		self.np_path = self.widgets.get_widget("np_path")
		self.np_path.set_text(self.newProject.path)
		self.np_platform = self.widgets.get_widget("np_platform")

		platform_entry_box = gtk.ListStore(gobject.TYPE_STRING)
		for pname in SDK().platforms.keys():
			platform_entry_box.append([pname])
			
		self.np_platform.set_model(platform_entry_box)
		self.np_platform.set_text_column(0)
		self.np_platform.child.set_text(platform_entry_box[0][0])
		
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

