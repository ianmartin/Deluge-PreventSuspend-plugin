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

import gobject

import deluge
from deluge.plugins.corepluginbase import CorePluginBase
import deluge.component as component
from deluge.log import LOG as log

plugin_name = "Prevent Suspend"
plugin_author = "Andreas Dalsgaard"
plugin_version = "0.1"
plugin_description = _("""
Make deluge prevent the computer from suspending or hibernating""")

DEFAULT_PREFS= {
	"enabled": True,
	"preventwhen": 1
}


def check_state(states):
	"""Returns true if at least one of the torrents is in one of the states in states[]"""
	status = component.get("Core").export_get_torrents_status(None, ["state"])
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

### PLUGIN ###

class Core(CorePluginBase):	
	def enable(self):
		log.info("Enable Prevent Suspend core plugin")
		self.config = deluge.configmanager.ConfigManager("preventsuspend.conf", DEFAULT_PREFS)
      
                self.dev = None
                self.cookie = None
		self.update_timer = None

		self.update()
	
	def disable(self):
		log.info("Disable Prevent Suspend core plugin")
		self.stop_timer()
		self.config.save()
		self.allow_sleep()
		self.dev = None

	def start_timer(self):
		if self.update_timer is None:
			self.update_timer = gobject.timeout_add(10000, self.update)
			log.debug("time started")

	def stop_timer(self):
		if self.update_timer is not None:
			gobject.source_remove(self.update_timer)
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
		if self.config["enabled"]:
			self.start_timer()
			if self.should_inhibit():
				self.inhibit_sleep()
			else:
				self.allow_sleep()
		else:
			self.stop_timer()
			self.allow_sleep()
		return True
		
	#Pretty much stolen from update-manager and modified to fit including fixing
	# bug https://bugs.launchpad.net/bugs/140754
	def inhibit_sleep(self):
		"""
		Send a dbus signal to power-manager to not suspend
		the system, try both the new freedesktop and the
		old gnome dbus interface
		"""

		if self.cookie is not None:
			return True

		if self.dev is not None:
			return self.dev.Inhibit()

		try:
			return self._inhibit_sleep_new_interface()
		except Exception, e:
			log.debug("Could not send the dbus Inhibit signal using freedesktop interface: %s" % e)
		
		try:
			return self._inhibit_sleep_old_interface()
		except Exception, e:
			log.debug("Could not send the dbus Inhibit signal using gnome interface: %s" % e)

		return False

	def allow_sleep(self):
		"""Send a dbus signal to gnome-power-manager to allow a suspending
		the system"""
		if self.dev is not None:
			if self.cookie is not None:
				try:
					self.dev.UnInhibit(self.cookie)
				except Exception, e:
					log.error("Unable to send the dbus UnInhibit signal: %s" % e)
				self.cookie = None

	def _inhibit_sleep_old_interface(self):	
		"""
		Send a dbus signal to org.gnome.PowerManager to not suspend
		the system, this is to support pre-gutsy
		"""
		import dbus
		bus = dbus.SessionBus()
		devobj = bus.get_object('org.gnome.PowerManager', 
								'/org/gnome/PowerManager')
		self.dev = dbus.Interface(devobj, "org.gnome.PowerManager")
		self.cookie = self.dev.Inhibit('Deluge', 'Downloading torrents')
		return True

	def _inhibit_sleep_new_interface(self):
		"""
		Send a dbus signal to gnome-power-manager to not suspend
		the system
		"""
		import dbus
		bus = dbus.SessionBus()
		devobj = bus.get_object('org.freedesktop.PowerManagement', 
								'/org/freedesktop/PowerManagement/Inhibit')
		self.dev = dbus.Interface(devobj, "org.freedesktop.PowerManagement.Inhibit")
		self.cookie = self.dev.Inhibit('Deluge', 'Downloading torrents')
		return True


	def export_get_config(self):
		"""Returns the config dictionary"""
		return self.config.config

	def export_set_config(self, config):
		"""Sets the config based on values in 'config'"""
		for key in config.keys():
			self.config[key] = config[key]
		self.update()
