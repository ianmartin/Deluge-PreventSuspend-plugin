#
# core.py
#
# Copyright (C) 2008 Andreas Dalsgaard <andreas.dalsgaard@gmail.com>
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
#
# This is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#

from twisted.internet.task import LoopingCall

import deluge
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
from deluge.log import LOG as log
from deluge.core.rpcserver import export


DEFAULT_PREFS= {
	"enabled": True,
	"preventwhen": 1
}

APPNAME = "Deluge"
REASON = 'Downloading torrents'

def check_state(states):
	"""Returns true if at least one of the torrents is in one of the states in states[]"""
	status = component.get("Core").get_torrents_status(None, ["state"])
	in_states = False
	for torrent in status:
		if status[torrent]["state"] in states:
			in_states = True
			exit
	return in_states

def downloading():
	"""Return true if at least one torrent is downloading"""
	status = check_state(["Downloading"])
	log.debug("Downloading status: %s" % status)
	return status

def downloading_or_seeding():
	"""Return true if at least one torrent is downloading or seeding"""
	status = check_state(["Downloading", "Seeding"])
	log.debug("downloading or seeding status: %s" % status)
	return status

class DBusInhibitor:
	def __init__(self, name, path, interface, method=["Inhibit", "UnInhibit"]):
		self.name = name
		self.path = path
		self.interface_name = interface
		
		import dbus
		bus = dbus.SessionBus()
		devobj = bus.get_object(self.name, self.path)
		self.iface = dbus.Interface(devobj, self.interface_name)
		# Check we have the right attributes
		self._inhibit = getattr(self.iface, method[0])
		self._uninhibit = getattr(self.iface, method[1])

	def inhibit(self):
		self.cookie = self._inhibit(APPNAME, REASON)

	def uninhibit(self):
		self._uninhibit(self.cookie)

class GnomeSessionInhibitor(DBusInhibitor):
	TOPLEVEL_XID = 0
	INHIBIT_SUSPEND = 4
	def __init__(self):
		DBusInhibitor.__init__(self, 'org.gnome.SessionManager',
				             '/org/gnome/SessionManager',
				             "org.gnome.SessionManager",
				             ["Inhibit", "Uninhibit"])

	def inhibit(self):
		self.cookie = self._inhibit(APPNAME,
					    GnomeSessionInhibitor.TOPLEVEL_XID,
					    REASON,
					    GnomeSessionInhibitor.INHIBIT_SUSPEND)

### PLUGIN ###

class Core(CorePluginBase):	
	def enable(self):
		log.info("Prevent Suspend core plugin enabled")
		self.config = deluge.configmanager.ConfigManager("preventsuspend.conf", DEFAULT_PREFS)
      
                self.inhibited = False
		self.update_timer = None


		self.inhibitor = self._get_inhibitor()

		self.update()
	
	def disable(self):
		log.info("Prevent Suspend core plugin disabled")
		self.stop_timer()
		if self.inhibitor is not None:
			if self.inhibited: 
				self.inhibitor.uninhibit()
			del self.inhibitor
			self.inhibitor = None
		self.config.save()

	def start_timer(self):
		if self.update_timer is None:
			self.update_timer = LoopingCall(self.update)
			self.update_timer.start(10)
			log.debug("time started")

	def stop_timer(self):
		if self.update_timer is not None:
			self.update_timer.stop()
			log.debug("time stopped")
			self.update_timer = None

	def should_inhibit(self):
		inhibit = False
		if self.config["preventwhen"] == 0:
			inhibit = downloading()
		elif self.config["preventwhen"] == 1:
			inhibit	 = downloading_or_seeding()
		elif self.config["preventwhen"] == 2:
			inhibit = True
		return inhibit

	def update(self):
		if self.inhibitor is None:
			return False

		if self.config["enabled"]:
			self.start_timer()
			if self.should_inhibit():
				if not self.inhibited:
					self.inhibitor.inhibit()
					self.inhibited = True
			else:
				if self.inhibited:
					self.inhibitor.uninhibit()
					self.inhibited = False
		else:
			self.stop_timer()
			if self.inhibited:
				self.inhibitor.uninhibit()
				self.inhibited = False
		return True

	def _get_inhibitor(self):
		try:
			return GnomeSessionInhibitor()
		except Exception as e:
			log.debug("Could not initialise the gnomesession interface: %s" % e)
		
		try:
			return DBusInhibitor('org.freedesktop.PowerManagement', 
					     '/org/freedesktop/PowerManagement/Inhibit',
					     'org.freedesktop.PowerManagement.Inhibit')
		except Exception, e:
			log.debug("Could not initialise the freedesktop interface: %s" % e)
		
		try:
			return DBusInhibitor('org.gnome.PowerManager', 
					     '/org/gnome/PowerManager',
					     'org.gnome.PowerManager')
		except Exception, e:
			log.debug("Could not initialise the gnome interface: %s" % e)

		return None
	
	@export
	def get_config(self):
		"""Returns the config dictionary"""
		out = self.config.config
		out["_can_inhibit"] = self.inhibitor is not None
		return out

	@export
	def set_config(self, config):
		"""Sets the config based on values in 'config'"""
		for key in config.keys():
			self.config[key] = config[key]
		self.update()
