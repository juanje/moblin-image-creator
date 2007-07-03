#!/usr/bin/python

from Tkinter import *
from SDK import *

class mylist(Frame):

	def __init__(self, parent=None):
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)
		self.makeList()

	def handlList(self, event):
		index = self.listbox.curselection()
		label = self.listbox.get(index)
		self.PrintList(label)

	def makeList(self):
		list = Listbox(self, relief=SUNKEN)
		list.pack(side=LEFT, expand=YES, fill=BOTH)

		pos = 0
		sdk=SDK()
		for key in sdk.projects.keys():
			project=sdk.projects[key]
			list.insert(pos, project.name)
			print 'found: %s ' % (project.name)
			pos += 1
		list.bind('<Double-1>', self.handlList)
		self.listbox = list

		Button(self, text="Close", compound=CENTER, command=self.quit).pack()

	def PrintList(self, project):
		print 'You selected: ',  project
		self.quit()

if __name__ == '__main__' :
	mylist().mainloop()
