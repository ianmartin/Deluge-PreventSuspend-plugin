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

from deluge.plugins.corepluginbase import CorePluginBase
from deluge.log import LOG as log

plugin_name = "Prevent Suspend"
plugin_author = "Andreas Dalsgaard"
plugin_version = "0.1"
plugin_description = _("""
Make deluge prevent the computer from suspending or hibernating""")



### PLUGIN ###

class Core(CorePluginBase):	
	def enable(self):
		log.info("Enable Prevent Suspend core plugin")
                self.dev = None
                self.cookie = None
		result = self.inhibit_sleep()
		
		log.debug("Inhibit result: %s" % result)
		if result == False:
			log.error("Unable to inhibit suspend")
	
	def disable(self):
		log.info("Disable Prevent Suspend core plugin")
		self.allow_sleep()
		self.dev = None
	
	#Pretty much stolen from update-manager and modified to fit including fixing
	# bug https://bugs.launchpad.net/bugs/140754
	def inhibit_sleep(self):
		"""
		Send a dbus signal to power-manager to not suspend
		the system, try both the new freedesktop and the
		old gnome dbus interface
		"""
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
			else:
				log.debug("No cookie")
		else:
			log.debug("No bus")

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


