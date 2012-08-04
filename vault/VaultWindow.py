# -*- Mode: Python3; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('vault')

from gi.repository import Gtk # pylint: disable=E0611
from gi.repository import Gio # pylint: disable=E0611

import logging
logger = logging.getLogger('vault')

from vault_lib import Window
from vault.AboutVaultDialog import AboutVaultDialog
from vault.PreferencesVaultDialog import PreferencesVaultDialog
from vault import FieldsDialog
from vault import PasswordDialog
from vault import ChangepasserrorDialog
from vault import OpenerrorDialog
from vault import PassworderrorDialog
from vault import UnmounterrorDialog
from vault import DeleteerrorDialog
from vault import CreateerrorDialog
from vault import OpenpasswordDialog
from vault import UnmountingproblemDialog
from vault import ForcecloseDialog
from vault import ChangepasswordDialog
from vault import InfoDialog

import sys
import platform
import os
import signal
import subprocess
import shlex
import shutil
import pickle
import re
import time
import tempfile
import webbrowser

HOME = os.getenv("HOME")
ECHO = "/bin/echo"
ENCFS = "/usr/bin/encfs"
ENCFSCTL = "/usr/bin/encfsctl"
FUSERMOUNT = "/bin/fusermount"
MOUNT = "/bin/mount"
efolders = HOME + '/.config/vault/existing_folders.data'
ofolders = HOME + '/.config/vault/open_folders.data'


# See vault_lib.Window.py for more details about how this class works
class VaultWindow(Window):
    __gtype_name__ = "VaultWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(VaultWindow, self).finish_initializing(builder)

        self.AboutDialog           = AboutVaultDialog
        self.PreferencesDialog     = PreferencesVaultDialog
        self.FieldsDialog 		   = FieldsDialog.FieldsDialog()
        self.PasswordDialog 	   = PasswordDialog.PasswordDialog()
        self.ChangePassErrorDialog = ChangepasserrorDialog.ChangepasserrorDialog()
		self.OpenErrorDialog	   = OpenerrorDialog.OpenerrorDialog()
		self.PasswordErrorDialog   = PassworderrorDialog.PassworderrorDialog()
		self.UnmountErrorDialog    = UnmounterrorDialog.UnmounterrorDialog()
		self.DeleteErrorDialog     = DeleteerrorDialog.DeleteerrorDialog()
		self.CreateErrorDialog     = CreateerrorDialog.CreateerrorDialog()
		self.OpenPasswordDialog    = OpenpasswordDialog.OpenpasswordDialog()
		self.UnmountingDialog      = UnmountingproblemDialog.UnmountingproblemDialog()
		self.ForceCloseDialog	   = ForcecloseDialog.ForcecloseDialog()
		self.ChangePasswordDialog  = ChangepasswordDialog.ChangepasswordDialog()
		self.InfoDialog			   = InfoDialog.InfoDialog()

        self.load_files()
        self.set_folders()
        
        self.settings = Gio.Settings("net.launchpad.vault")
        self.filemanager = self.settings.get_string("file-manager")
        self.boolean = self.settings.get_boolean("delete-folders")
        self.set_settings(self.boolean)
        
        notebook = self.builder.get_object("notebook")
        notebook.set_current_page(1)
        
        combobox = self.builder.get_object("modecombobox")
        combobox.set_active(0)
        
        # Code for other initialization actions should be added here
				
	def create_folder(self, param=None):
		
		combobox = self.builder.get_object("modecombobox")
		modestore = self.builder.get_object("modestore")
		name_entry = self.builder.get_object("open_name_entry")
		
		self.PasswordDialog.ui.label3.set_visible(False)
		
		text = name_entry.get_text()
		
		if name_entry.get_text_length() is 0:
			self.FieldsDialog.run()
			self.FieldsDialog.hide()
			return
			
		if self.folder_exist(text) == True:
            self.CreateErrorDialog.run()
            self.CreateErrorDialog.hide()
		else:
			mode = combobox.get_active()
			foldername = unicode(text)
			location = HOME + '/' + foldername
			enfolder = HOME + '/.' + foldername
            name_entry.set_text("")
            
            if not os.path.exists(location):
                os.mkdir(location, 0700)
            if not os.path.exists(enfolder):
                os.mkdir(enfolder, 0700)
            
            response = self.PasswordDialog.run()
            self.PasswordDialog.hide()
            print response
            if response == -5:
                self.pass1 = self.PasswordDialog.ui.password_entry.get_text()
                self.pass2 = self.PasswordDialog.ui.confirm_password_entry.get_text()
                r = self.check_pass()
                if r is False:
					self.PasswordDialog.ui.password_entry.set_text("")
					self.PasswordDialog.ui.confirm_password_entry.set_text("")
					return False
            elif response == -4 or response == -6:
				self.PasswordDialog.ui.password_entry.set_text("")
				self.PasswordDialog.ui.confirm_password_entry.set_text("")
				return False

                
            tmp = tempfile.mkstemp()[1]
            with open(tmp, 'w') as f:
                f.write(self.pass1)
            extpass = "/bin/cat %s" % (tmp)
            if mode is 0:
                p2 = subprocess.Popen([ENCFS, "--standard", "--extpass", extpass, enfolder, location],
                                      stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                      stderr=subprocess.STDOUT)
                output = p2.communicate()[0]
            else:
                p2 = subprocess.Popen([ENCFS, "--extpass", extpass, enfolder, location],
                                      stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                      stderr=subprocess.STDOUT)
                output = p2.communicate(input="\n\n")[0]
            os.remove(tmp)
            while p2.poll() is None:
                time.sleep(1)
            if p2.poll() == 0:
                subprocess.call([self.filemanager, location])
                
                self.load_files()
                self.efoldersdata.append(foldername)
                f = open(efolders, 'wb')
                pickle.dump(self.efoldersdata, f)
                f.close()
                self.ofoldersdata.append(foldername)
                f = open(ofolders, 'wb')
                pickle.dump(self.ofoldersdata, f)
                f.close()

                openstore = self.builder.get_object("foldersstore")
                openstore.append([unicode(text)])
                closestore = self.builder.get_object("openfoldersstore")
                closestore.append([unicode(text)])
            else:
                self.CreateErrorDialog.run()
                self.CreateErrorDialog.hide()
                
	
	def open_folder(self, widget, path, param=None):
        folder = self.get_selected_folder("open")
        foldername = unicode(folder)
        self.path = HOME + '/' + foldername
        enfolder = HOME + '/.' + foldername
        if self.is_mounted(self.path) is False:
            if not os.path.exists(self.path):
                os.mkdir(self.path)
            response = self.OpenPasswordDialog.run()
            self.OpenPasswordDialog.hide()
            if response == -5:
                passwd = self.OpenPasswordDialog.ui.open_password_entry.get_text()
                self.OpenPasswordDialog.ui.open_password_entry.set_text("")
            p1 = subprocess.Popen([ECHO, passwd], stdout=subprocess.PIPE)
            p2 = subprocess.Popen([ENCFS, "-S", enfolder, self.path], stdin=p1.stdout, stdout=subprocess.PIPE)
            p3 = p2.communicate()[0]
            if p2.poll() is not 0:
                self.PasswordErrorDialog.run()
                self.PasswordErrorDialog.hide()
            else:
                subprocess.call([self.filemanager, self.path])
                self.load_files()
                self.ofoldersdata.append(foldername)
                f = open(ofolders, 'wb')
                pickle.dump(self.ofoldersdata, f)
                f.close()
                store = self.builder.get_object("openfoldersstore")
                store.append([foldername])
        else:
            self.OpenErrorDialog.run()
            self.OpenErrorDialog.hide()
            
    
    def close_folder(self, widget, path, param=None):
        text = self.get_selected_folder("close")
        foldername = unicode(text)
        location = HOME + '/' + foldername
        p1 = subprocess.Popen([FUSERMOUNT, "-u", location], stdin=None, stdout=subprocess.PIPE)
        while p1.poll() is None:
            time.sleep(1)
        if p1.returncode is not 0:
            reply = self.UnmountErrorDialog.show()
            slef.UnmountErrorDialog.hide()
            if reply == -5:
                p1 = subprocess.Popen([FUSERMOUNT, "-z", "-u", location], stdin=None, stdout=subprocess.PIPE)
                p2 = p1.communicate()[0]
            else:
                self.ForceCloseDialog.run()
                self.ForceCloseDialog.hide()
                p1 = subprocess.Popen([FUSERMOUNT, "-u", location], stdin=None, stdout=subprocess.PIPE)
                p2 = p1.communicate()[0]
            if p1.poll() is not 0:
                self.UnmountingDialog.run()
                self.UnmountingDialog.hide()
            else:
                self.close_commands(location, foldername)
        else:
            self.close_commands(location, foldername)
            
            
    def close_commands(self, location, folder):
		checkbutton = self.builder.get_object("deletemountpoint_close_checkbutton")
        if checkbutton.get_active():
            try:
                shutil.rmtree(location, True)
            except IOError:
                pass
        self.load_files()
        for name in self.ofoldersdata:
            if name == folder:
                self.ofoldersdata.remove(folder)
        f = open(ofolders, 'wb')
        pickle.dump(self.ofoldersdata, f)
        f.close()
        self.remove_item("close", folder)
        
        
    def delete_folder(self, widget, path, param=None):
        """Delete selected folder"""
        text = self.get_selected_folder("open")
        foldername = unicode(text)
        folder = HOME + '/' + foldername
        enfolder = HOME + '/.' + foldername
        if self.is_mounted(folder) is False:
			checkbutton1 = self.builder.get_object("deletemountpoints_delete_checkbutton")
			checkbutton2 = self.builder.get_object("delete_enfolder_checkbutton")
            if checkbutton1.get_active():
                try:
                    shutil.rmtree(folder, True)
                except IOError:
                    pass
            if checkbutton2.get_active():
                try:
                    shutil.rmtree(enfolder, True)
                except IOError:
                    pass
            self.load_files()
            self.efoldersdata.remove(foldername)
            f = open(efolders, 'wb')
            pickle.dump(self.efoldersdata, f)
            f.close()
            self.remove_item("open", foldername)
        else:
            self.DeleteErrorDialog.run()
            self.DeleteErrorDialog.hide()
        
        
    def popup_window(self, treeview, event):
		if event.button == 3:
			popup = self.builder.get_object("menu3")
			treeview = self.builder.get_object("opentreeview")
			time = event.time
			popup.popup(None, None, None, None, event.button, time)
			
	
	def donateitem_activated(self, item, param=None):
		webbrowser.open_new_tab("https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=EHPKLVK79J4E8")
            

	def get_selected_folder(self, mode):
		if mode == "open":
			tree = self.builder.get_object("opentreeview")
		elif mode == "close":
			tree = self.builder.get_object("closetreeview")
		elif mode == "delete":
			tree = self.builder.get_object("deletetreeview")
			
		selection = tree.get_selection()
		treemodel, treeiter = selection.get_selected()
		value = treemodel.get_value(treeiter, 0)
		return value

	def remove_item(self, tab, folder):
		if tab == "open":
			store = self.builder.get_object("foldersstore")
		elif tab == "close":
			store = self.builder.get_object("openfoldersstore")
		
		for row in store:
			if row[0] == folder:
				store.remove(row.iter)

	
	def folder_exist(self, name):
        """Check if folder exists"""
        self.load_files() 
        name = unicode(name)
        if name in self.efoldersdata:
            return True
        else:
            return False
            
            
    def is_mounted(self, path):
        """Test if a folder is mounted"""
        p = subprocess.Popen([MOUNT], stdout=subprocess.PIPE)
        p = p.communicate()[0]
        p = p.split("\n")
        
        r = re.compile("^encfs on %s type fuse" % path)
        for l in p:
            if r.match(l):
                return True
        return False
        
        
    def folder_info(self, button, param=None):
		folder = self.get_selected_folder("open")
        location = HOME + '/.' + folder
        output = subprocess.Popen([ENCFSCTL, 'info', location], stdout=subprocess.PIPE)
        final_output = output.stdout.read()
        info = unicode(final_output, "utf-8")
        self.settings.set_string("info", info)
        self.InfoDialog.run()
        self.InfoDialog.hide()
        
        
    def change_password(self, button, param=None):
		folder = self.get_selected_folder("open")
		enfolder = HOME + "/." + folder
		response = self.ChangePasswordDialog.run()
		self.ChangePasswordDialog.hide()
		print response
		if response == -5:
			c_password = self.ChangePasswordDialog.ui.current_password_entry.get_text()
			n_password = self.ChangePasswordDialog.ui.new_password.get_text()
			cn_password = self.ChangePasswordDialog.ui.confirm_password.get_text()
			r = self.check_change_password( n_password, cn_password )
            
            if r is False:
				self.ChangePasswordDialog.ui.new_password.set_text("")
				self.ChangePasswordDialog.ui.confirm_password.set_text("")
				return False
			
			p1 = subprocess.Popen([ECHO, "-e", c_password + "\n" + n_password + "\n"],\
				stdout=subprocess.PIPE)
			p2 = subprocess.Popen([ENCFSCTL, "autopasswd", enfolder],\
				stdin=p1.stdout, stdout=subprocess.PIPE)
			p2.communicate()[0]
			if p2.poll() is not 0:
				self.ChangePassErrorDialog.run()
				self.ChangePassErrorDialog.hide()
		elif response == -4:
			return False
		else:
			self.ChangePassErrorDialog.run()
			self.ChangePassErrorDialog.hide()
        
            
    def check_pass(self):
        """Check if passwords match"""
        while self.pass1 != self.pass2:
			self.PasswordDialog.ui.label3.set_visible(True)
			self.PasswordDialog.ui.password_entry.set_text("")
			self.PasswordDialog.ui.confirm_password_entry.set_text("")
            response = self.PasswordDialog.run()
            self.PasswordDialog.hide()
            if response != -5:
				return False
			else:
				self.check_pass()


	def check_change_password(self, n_password, cn_password):
		while n_password != cn_password:
			self.ChangePasswordDialog.ui.label4.set_visible(True)
			self.ChangePasswordDialog.ui.current_password_entry.set_text("")
			self.ChangePasswordDialog.ui.new_password.set_text("")
			self.ChangePasswordDialog.ui.confirm_password.set_text("")
            response = self.ChangePasswordDialog.run()
            self.ChangePasswordDialog.hide()
            if response != -5:
				return False
			else:
				pass1 = self.ChangePasswordDialog.ui.new_password.get_text()
				pass2 = self.ChangePasswordDialog.ui.confirm_password.get_text()
				self.check_change_pass(pass1, pass2)
            
            
	def load_files(self):
        """Load lists of folders"""
        self.efoldersdata = []
        self.ofoldersdata = []
        try:
            f = open(efolders, 'rb')
        except IOError:
            print "File don't exist"
        try:
            self.efoldersdata = pickle.load(f)
        except (EOFError, IOError):
            pass
        f.close()
        try:
            f = open(ofolders, 'rb')
        except IOError:
            print "File don't exist"
        try:
            self.ofoldersdata = pickle.load(f)
        except (EOFError, IOError):
            pass
        f.close()

        
	def set_folders(self):
		folders_store = self.builder.get_object("foldersstore")
		open_folders_store = self.builder.get_object("openfoldersstore")
		
		folders_store.clear()
		for i in self.efoldersdata:
			folders_store.append([i])
		
		open_folders_store.clear()
		for i in self.ofoldersdata:
			open_folders_store.append([i])
			
	def set_settings(self, boolean):
		checkbutton1 = self.builder.get_object("deletemountpoints_delete_checkbutton")
		checkbutton2 = self.builder.get_object("deletemountpoint_close_checkbutton")
		if boolean is True:
			checkbutton1.set_active(False)
			checkbutton2.set_active(False)
		else:
			checkbutton1.set_active(True)
			checkbutton2.set_active(True)
