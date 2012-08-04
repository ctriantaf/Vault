# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

# This is your preferences dialog.
#
# Define your preferences in
# data/glib-2.0/schemas/net.launchpad.vault.gschema.xml
# See http://developer.gnome.org/gio/stable/GSettings.html for more info.

from gi.repository import Gio # pylint: disable=E0611

import gettext
from gettext import gettext as _
gettext.textdomain('vault')

import logging
logger = logging.getLogger('vault')

from vault_lib.PreferencesDialog import PreferencesDialog

class PreferencesVaultDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesVaultDialog"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the preferences dialog"""
        super(PreferencesVaultDialog, self).finish_initializing(builder)

        # Bind each preference widget to gsettings
        settings = Gio.Settings("net.launchpad.vault")
        widget = self.builder.get_object('file_manager_entry')
        widget2 = self.builder.get_object("checkbutton")
        settings.bind("file-manager", widget, "text", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("delete-folders", widget2, "active", Gio.SettingsBindFlags.DEFAULT)

        # Code for other initialization actions should be added here.
        
    
		
		
		
		
		
