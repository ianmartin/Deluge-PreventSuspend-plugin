#
# __init__.py
#
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

from deluge.log import LOG as log
from deluge.plugins.init import PluginBase

class CorePlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        try:
            from core import Core
            self.plugin = Core(plugin_api, plugin_name)
        except Exception, e:
            log.error("Failed to load  PreventSuspend core plugin: %s", e)


class GtkUIPlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        # Load the GtkUI portion of the plugin
        try:
            from gtkui import GtkUI
            self.plugin = GtkUI(plugin_api, plugin_name)
        except Exception, e:
            log.error("Failed to load PreventSuspend gtk ui plugin: %s", e)
