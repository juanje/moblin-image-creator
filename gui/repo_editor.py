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


_ = gettext.lgettext


class repoEditor(object):
    """Class to assist in Repository editing"""
    def __init__(self, sdk, repoPath):
        self.sdk = sdk
        self.repoPath = repoPath

        self.gladefile = os.path.join(self.sdk.path, "image-creator.glade")
        self.editRepoTree = gtk.glade.XML(self.gladefile, 'yumRepoDialog')
        self.editRepoDialog = self.editRepoTree.get_widget('yumRepoDialog')
        self.editRepoDialog.set_size_request(750, 200)

        self.repoNameEntry = self.editRepoTree.get_widget('repo_name_entry')
        self.repoUrlEntry = self.editRepoTree.get_widget('repo_url_entry')
        self.failovermethodEntry = self.editRepoTree.get_widget('failovermethod_entry')
        self.repoEnabledEntry = self.editRepoTree.get_widget('repo_enabled_entry')
        
        self.addButton = self.editRepoTree.get_widget('add_button')
        self.addButton.connect('clicked', self.add_button_clicked)
        self.removeButton = self.editRepoTree.get_widget('remove_button')
        self.removeButton.connect('clicked', self.remove_button_clicked)
        self.saveButton = self.editRepoTree.get_widget('save_button')
        self.saveButton.connect('clicked', self.save_button_clicked)

        self.repoListView = self.editRepoTree.get_widget('repoList')
        self.repoListView.get_selection().connect('changed', self.repoList_callback)

        cellRenderC0 = gtk.CellRendererText()
        col0 = gtk.TreeViewColumn(_("Repository List"), cellRenderC0)
        self.repoListView.append_column(col0)

        col0.add_attribute(cellRenderC0, 'text', 0)
        col0.set_resizable(True)

        self.repoListView.set_headers_clickable(True)
        self.repoList = gtk.TreeStore(gobject.TYPE_STRING)
        self.repoListView.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.repoListView.set_model(self.repoList)
        
        self.current_repo = ""
        self.create_repo_list()    

    def create_repo_list(self):
        self.repoList = gtk.TreeStore(gobject.TYPE_STRING)
        self.repoListView.set_model(self.repoList)

        repo_list = self.get_repo_list()
        if repo_list:
            for repo in repo_list:
                self.repoList.append(None, [repo])

    def repoList_callback(self, widget):

        self.repoNameEntry.set_text("")
        self.repoUrlEntry.set_text("")
        self.repoEnabledEntry.set_text("")
        self.failovermethodEntry.set_text("")

        num_rows_selected = self.repoListView.get_selection().count_selected_rows()
        if num_rows_selected == 1:
            self.removeButton.set_sensitive(True)
            self.saveButton.set_sensitive(True)
            self.repoNameEntry.set_sensitive(True)
            self.repoUrlEntry.set_sensitive(True)
            self.failovermethodEntry.set_sensitive(True)
            self.repoEnabledEntry.set_sensitive(True)
            model, treePathList = self.repoListView.get_selection().get_selected_rows()   
            if os.path.isfile(os.path.join(self.repoPath, model[treePathList[0]][0])):
                repo = open(os.path.join(self.repoPath, model[treePathList[0]][0]))
                self.current_repo = model[treePathList[0]][0]
                for line in repo:
                    if line.find("name") != -1:
                        repoName = line.split('=')[1]
                        self.repoNameEntry.set_text(repoName.rstrip())
                    if line.find("baseurl") != -1:
                        repoUrl = line.split('=')[1]
                        self.repoUrlEntry.set_text(repoUrl.rstrip())
                    if line.find("enabled") != -1:
                        repoEnabled = line.split('=')[1]
                        self.repoEnabledEntry.set_text(repoEnabled.rstrip())
                    if line.find("failovermethod") != -1:
                        repoFailovermethod = line.split('=')[1]
                        self.failovermethodEntry.set_text(repoFailovermethod.rstrip())
        else:
            self.current_repo = ""
            self.removeButton.set_sensitive(False)
            self.saveButton.set_sensitive(False)
            self.repoNameEntry.set_sensitive(False)
            self.repoUrlEntry.set_sensitive(False)
            self.failovermethodEntry.set_sensitive(False)
            self.repoEnabledEntry.set_sensitive(False)


    
    def get_repo_list(self):
        repoList = []
        if os.path.isdir(self.repoPath):
            for filename in os.listdir(self.repoPath):
                if os.path.isfile(os.path.join(self.repoPath, filename)):
                    repoList.append(filename)        
        return repoList

    def add_button_clicked(self, widget):
        widgets = gtk.glade.XML(self.gladefile, 'new_img_dlg')
        widgets.get_widget('img_name_lbl').set_text(_("New Repo Name"))
        repoNameEntry = widgets.get_widget('img_name')
        dialog = widgets.get_widget('new_img_dlg')
        dialog.set_title(_("Add New Repo"))
        dialog.set_default_response(gtk.RESPONSE_OK)
        result = dialog.run()
        repoName = repoNameEntry.get_text()
        if repoName.find(".repo") == -1:
            repoName = repoName + ".repo"
        dialog.destroy()
        if result == gtk.RESPONSE_OK and repoName:                
                #Create an empty file
                if not os.path.isfile(os.path.join(self.repoPath, repoName)):
                    repoFile = open(os.path.join(self.repoPath, repoName), 'w')                
                    repoFile.write("[%s]\n" % repoName)
                    repoFile.close()
                    self.create_repo_list()

                selection = self.repoListView.get_selection()
                for count, row in enumerate(self.repoList):
                    name = row[0]
                    if name == repoName:
                        selection.select_path(count)


    def remove_button_clicked(self, widget):
        model, treePathList = self.repoListView.get_selection().get_selected_rows()   
        if os.path.isfile(os.path.join(self.repoPath, model[treePathList[0]][0])):
            print _("Removing Repo: %s") % model[treePathList[0]][0]
            os.unlink(os.path.join(self.repoPath, model[treePathList[0]][0]))
            self.create_repo_list()

    def save_button_clicked(self, widget):
        print _("Saving: %s") % self.current_repo
        repoFile = open(os.path.join(self.repoPath, self.current_repo))
        fileContent = repoFile.readlines()
        nameWritten = False
        urlWritten = False
        failovermethodWritten = False
        enabledWritten = False

        repoFile.close()
        repoFile = open(os.path.join(self.repoPath, self.current_repo), "w")
        for line in fileContent:
            if line.find("name") != -1:
                repoFile.write("name=%s\n" % self.repoNameEntry.get_text())
                nameWritten = True
            elif line.find("baseurl") != -1:
                repoFile.write("baseurl=%s\n" % self.repoUrlEntry.get_text())
                urlWritten = True
            elif line.find("enabled") != -1:
                repoFile.write("enabled=%s\n" % self.repoEnabledEntry.get_text())
                enabledWritten = True
            elif line.find("failovermethod") != -1:
                repoFile.write("failovermethod=%s\n" % self.failovermethodEntry.get_text())
                failovermethodWritten = True
            else:
                repoFile.write(line)
            if not nameWritten:
                repoFile.write("name=%s\n" % self.repoNameEntry.get_text())
            if not failovermethodWritten:
                repoFile.write("failovermethod=%s\n" % self.failovermethodEntry.get_text())
            if not urlWritten:
                repoFile.write("baseurl=%s\n" % self.repoUrlEntry.get_text())
            if not enabledWritten:
                repoFile.write("enabled=%s\n" % self.repoEnabledEntry.get_text())
        repoFile.close()
    
    def run(self):
        result = self.editRepoDialog.run()
        if result == gtk.RESPONSE_OK:
            pass
        else:
            pass
        self.editRepoDialog.destroy()        

if __name__ == '__main__':
    sys.exit(main())
