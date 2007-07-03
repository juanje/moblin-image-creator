#!/usr/bin/python

from Tkinter import *
from tkMessageBox import *
from SDK import *

# FIXME callback temporary stub
def callback():
		print "FIXME"


#========================
#General Functions	=
#========================

def exit():
	main.destroy()

fields = 'Name', 'Path', 'Desc', 'Platform'

#Call SDK to create the project
def create_new_project(new_project, args):
	sdk = SDK()
	i = 0
	for arg in args:
		print "%s" % args[i].get()
		i +=1
		 
	proj = sdk.create_project(args[1].get(), args[0].get(), args[2].get(), sdk.platforms[args[3].get()])
	proj.install()

#Read in user input for New Project
def get_new_args(new_project, fields):

	entries = []
	for field in fields:
		row=Frame(new_project)
		lab=Label(row, width=8, text=field)
		ent=Entry(row)

		row.pack(side=TOP, fill=X)
		lab.pack(side=LEFT)
		ent.pack(side=RIGHT, expand=YES, fill=BOTH)
		entries.append(ent)
	return entries

def pCreateButtonHandler(new_project, args):
	create_new_project(new_project, args)
	new_project.destroy()

def new():
	new_project = Tk()
	new_project.title("Create New Project")
	#Read user input for project configuration & information
	args = get_new_args(new_project, fields)

	#Get platforms and list them
	Label(new_project, text="Supported Platforms").pack()
	sdk = SDK()
	_platforms = []
	pVar=StringVar()
	for p in sdk.platforms.keys():
		platform=sdk.platforms[p]
		print "Platforms found: %s" % (platform.name)
		_platforms.append(p)
		#Form an OptinMenu
	pVar.set(_platforms[0])
	pmenu=OptionMenu(new_project, pVar, *_platforms)
	pmenu.pack()



	new_project.bind('<Return>', (lambda event: create_new_project(args)))
	Button(new_project, text='Create',
			command= (lambda: pCreateButtonHandler(new_project, args))).pack(side=LEFT)
		#command= (lambda: create_new_project(new_project, args))).pack(side=LEFT)
	Button(new_project, text='Cancel', command=new_project.destroy).pack(side=RIGHT)

def open_project(p_list):
	index = p_list.curselection()
	label = p_list.get(index)
	print 'You selected:', label
	
	

def open():
	print "Open"
	sdk = SDK()
	p_list = Tk()
	projects_list = Listbox(p_list, relief=SUNKEN)
	
	for key in sdk.projects.keys():
		project=sdk.projects[key]
		print '%s ' % (project.name)
		projects_list.insert(END, project.name)
		projects_list.pack(side=BOTTOM, expand=YES, fill=BOTH)
	open = Button(p_list, text='Open', command=open_project).pack()	
	p_list.bind('<Double-1>',open(p_list))

def about():
	showinfo(
		"Aboue Intel eSDK",
		"eSDK is a developer tool developer by Intel's own OTC\n"
			"Tiger team: Rusty Lynch, Rob Rhoads, Tariq Shureih"
		)

#================
#file menu 	=
#================

def makeMenu(main):
	menu = Menu(main)
	main.config(menu=menu)
	filemenu = Menu(menu)

	menu.add_cascade(label="File", menu=filemenu)
	filemenu.add_command(label="New", command=new)
	filemenu.add_command(label="Open...", command=open)
	filemenu.add_separator()
	filemenu.add_command(label="Exit", command=sys.exit)

	menu.add_command(label="About", command=about)



#========================
#    Main		=
#========================

if __name__ == '__main__':
	main = Tk()
	main.title("Intel eSDK")
	
	makeMenu(main)

	#title
	logo = PhotoImage(file="./intel-logo.gif")
	r = Label(text = "\n\nIntel eSDK", fg="red", justify="left")
	r.pack(expand=YES, fill=BOTH)

	graphic = Label(main,image=logo)
	graphic.pack(side=TOP, expand=YES, fill=BOTH)

	body = Frame(main, width=500, height=400)
	body.pack()

	mainloop()

