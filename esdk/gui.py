#!/usr/bin/python

from Tkinter import *
from tkMessageBox import *
from SDK import *

# FIXME callback temporary stub
def callback():
		print "FIXME"

main = Tk()
main.title("Intel eSDK")

#title
logo = PhotoImage(file="./intel-logo.gif")
r = Label(text = "\n\nIntel eSDK", fg="red", justify="left")
r.pack(expand=YES, fill=BOTH)

graphic = Label(main,image=logo)
graphic.pack(side=TOP, expand=YES, fill=BOTH)
menu = Menu(main, tearoff=0)
menu.add_command(label="Undo", command=callback)
menu.add_command(label="Redo", command=callback)


#========================
#General Functions	=
#========================

def exit():
	main.destroy()

fields = 'Name', 'Path', 'Desc'#, 'Platform'

def create_new_project(new_project, args):
	sdk = SDK()
	print "%s" % args[0].get()
	proj = sdk.create_project(args[1].get(), args[0].get(), args[2].get(), sdk.platforms['donley'])
	proj.install()
	new_project.destroy

	

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

def get_platforms(new_project):
	Label(new_project, text="Platforms").pack(fill=BOTH)
	sdk = SDK()
	for key in sdk.platforms.keys():
		platform=sdk.platforms[key]
		print '%s ' % (platform.name)
		#platform_list.insert(END, "Test")
		#platform_list.pack(expand=YES, fill=BOTH)
		


def new():
	new_project = Tk()
	new_project.title("Create New Project")
	args = get_new_args(new_project, fields)
	#p = get_platforms(new_project)
	Label(new_project, text="Platforms").pack()
	p = Listbox(new_project, relief=SUNKEN)
	sdk = SDK()
	for key in sdk.platforms.keys():
		platform=sdk.platforms[key]
		print "%s" % (platform.name)
	new_project.bind('<Return>', (lambda event: create_new_project(args)))
	Button(new_project, text='Create',
		command= (lambda: create_new_project(new_project, args))).pack(side=LEFT)
	Button(new_project, text='Cancel', command=new_project.destroy).pack(side=RIGHT)

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
def about():
	showinfo(
		"Aboue Intel eSDK",
		"eSDK is a developer tool developer by Intel's own OTC\n"
			"Tiger team: Rusty Lynch, Rob Rhoads, Tariq Shureih"
		)

#================
#file menu 	=
#================
#def open():
	#showinfo(title="Open existing projcts", message= "Project 1\n Project 2")

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
#Platform		=
#========================

#Function Set Listbox

i = Label(main, text="Function Sets Available:\n", justify=LEFT)
i.pack()


func_sets = Listbox(main, selectmode=MULTIPLE)


for set in ["Internet", "Media", "Core", "Navigation"]:
	func_sets.insert(END, set)
func_sets.pack()

blank=Label(text = "\n\nFinal Image Output:")
blank.pack()

out = IntVar()
Radiobutton(main, text="ISO", variable = out, value=1).pack(anchor=W)
Radiobutton(main, text="Live CD", variable = out, value=0).pack(anchor=W)
Radiobutton(main, text="Live USB", variable = out, value=2).pack(anchor=W)

select_btn = Button(main, text="GO!")
select_btn.pack(side=LEFT, fill=X)

frame = Frame(main, width=100, height=100)
frame.bind("<Button-1>", callback)
frame.pack()

mainloop()

