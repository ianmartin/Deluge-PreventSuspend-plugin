#
# __init__.py
#
# Copyright (C) 2008 Andreas Dalsgaard <andreas.dalsgaard@gmail.com>
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

plugin_name = "Prevent Suspend"
plugin_author = "Andreas Dalsgaard"
plugin_version = "0.1"
plugin_description = _("""
Make deluge prevent the computer from suspending or hibernating""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return PreventSuspend(path, core, interface)


### PLUGIN ###

class PreventSuspend:	
	dev = None;
	cookie = None;

	def __init__(self, path, core, interface):	
		result = self.inhibit_sleep()
		
		if result == False:
			print("Warning: Could not inhibit")
	
	def unload(self):
		if self.dev != None and self.cookie != None:
			self.allow_sleep(self.dev, self.cookie)
	
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
			print "could not send the dbus Inhibit signal: %s" % e
			try:
				return self._inhibit_sleep_old_interface()
			except Exception, e:
				print "could not send the dbus Inhibit signal: %s" % e
			return False

	def allow_sleep(self, dev, cookie):
		"""Send a dbus signal to gnome-power-manager to allow a suspending
		the system"""
		try:
			self.dev.UnInhibit(cookie)
		except Exception, e:
			print "could not send the dbus UnInhibit signal: %s" % e


	def _inhibit_sleep_old_interface(self):	
		"""
		Send a dbus signal to org.gnome.PowerManager to not suspend
		the system, this is to support pre-gutsy
		"""
		import dbus
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
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
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		devobj = bus.get_object('org.freedesktop.PowerManagement', 
								'/org/freedesktop/PowerManagement/Inhibit')
		self.dev = dbus.Interface(devobj, "org.freedesktop.PowerManagement.Inhibit")
		self.cookie = self.dev.Inhibit('Deluge', 'Downloading torrents')
		return True


