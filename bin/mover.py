"""
Music Mover - move albums using ssh and scp.

Author: Daniel Nephin
Version: 0.3.1
Date: 2009-01-08

 TODO for version 0.4:
	- handle blank/of input on action inputs
	- thread it, so more albums can be queued while some transfer
	- prompt for accept unknown host key
	- TBD

 TODO long term
	- review code layout
	- nicer UI (with status bar)
	- self tunneling
	- allow remove remote files
	- allow push music as well
	- combine all sites into one listing

"""

from view import Menu, Message, Input, Color
from models import LocalMusic, RemoteSite
import jsonpickle
import sys
import re
import socket
import os


class Configuration(dict):
	"""
	Configuration object for the music mover. Takes care of serialization of the
	configuration as well as setting defaults.
	"""

	def __init__(self, **config_args):
		super(Configuration, self).__init__(self)
		# set defaults
		self['local_music']  = LocalMusic()
		self['sites'] = []

		# set values from command line
		self.serial_config_file = os.path.expanduser("~/.mediaMover/conf_json")
		if 'config_file' in config_args:
			self.serial_config_file = config_args['config_file']
		if 'color' in config_args:
			Color.color_on = False

	def load(self):
		" Load the config "
		# attempt load
		try:
			f_config = open(self.serial_config_file)
			config = jsonpickle.decode(f_config.read())
			self.update(config)
			f_config.close()
		except (IOError, ValueError):
			Message.err("No serialized config found, or error reading config.")
			return

		self['local_music'].refresh_album_cache()
		Message.note("Album cache refreshed")

	def save(self):
		" Save the config "
		# clear album cache
		self['local_music'].clear_album_cache()
		save_dir = os.path.expanduser("~/.mediaMover/")
		if not os.path.isdir(save_dir):
			os.mkdir(save_dir)
		# serialize the configuration
		f_config = open(self.serial_config_file, "w")
		json_string = jsonpickle.encode(self)
		f_config.write(json_string)
		f_config.close()



# imports for connectionManager
import paramiko
from paramiko.ssh_exception import SSHException
from stat import S_ISDIR 
import os
class ConnectionManager(object):
	" Manage a connection to an ssh server "
	
	dir_pattern = re.compile('/\w+')
	max_recurse = 3

	def __init__(self, remote_site, local_music):
		self.remote_site = remote_site
		self.password = None
		self.ssh_client = None
		self.scp_client = None
		self.connect()
		self.local_music = local_music
		self.recurse_count = 0

	def connect(self):
		" connect to the host "
		# ssh
		ssh_client = paramiko.SSHClient()
		ssh_client.load_system_host_keys()
		try:
			ssh_client.connect(self.remote_site.hostname, self.remote_site.port,
						self.remote_site.username, self.password)
		except SSHException, err:
			if self.password:
				raise SSHException("Password authentication failed: %s" % (err))
			Message.err("Connect failed: %s" % (err))
			self.password = Input.prompt_pass()	
			self.connect()

		if self.ssh_client == None:
			self.ssh_client = ssh_client
		if self.scp_client == None:
			transport = ssh_client.get_transport()
			self.scp_client = paramiko.SFTPClient.from_transport(transport)

		
	def disconnect(self):
		" disconnect from the host "
		if self.ssh_client:
			self.ssh_client.close()
		if self.scp_client:
			self.scp_client.close()

	def get_album_list(self):
		stdin, stdout, stderr = self.ssh_client.exec_command("ls -1 %s" % (
						" ".join(self.remote_site.get_dir_list())))
		error_list = map(lambda s: s.rstrip(), stderr.readlines())
		album_map = self._parse_album_list(stdout)
		return album_map, error_list

	def pull_album(self, path, file):
		" Pull an album over the local using sftp "
		target = path+file
		dest = self.local_music.get_save_dir().rstrip("/") + "/" + file
		# Check if target is a directory
		try:
			if S_ISDIR(self.scp_client.stat(target).st_mode):
				self._copy_dir(target, dest)
			else:
				# copy single file
				self.scp_client.get(target, dest)
		except (IOError, OSError), err:
			Message.err("Failed to move file %s: %s" % (file, err))


	def _copy_dir(self, remote_dir, dest):
		" copy a directory to local "
		if self.recurse_count >= self.max_recurse:
			return
		try:
			# mkdir on local
			os.mkdir(dest)
		except OSError, err:
			Message.err("Failed to create dir %s: %s" % (dest, err))
			return

		try:
			# loop through all files
			for sub_file in self.scp_client.listdir(path=remote_dir):
				path_sub_file = "%s/%s" % (remote_dir, sub_file)
				if S_ISDIR(self.scp_client.stat(path_sub_file).st_mode):
					# recurse into directories
					self.recurse_count += 1
					self._copy_dir(path_sub_file, "%s/%s" % (dest, sub_file))
					self.recurse_count -= 1
					continue

				# copy the file then
				self.scp_client.get(path_sub_file, "%s/%s" % (dest, sub_file))
		except (IOError, OSError), err:
			Message.err("Failed to move file(s) %s: %s" % (sub_file, err))


	def _parse_album_list(self, stdout):
		" Parse the directory listing into a map "
		active_dir = self.remote_site.get_dir_list()[0]
		album_map = {} 
		for line in stdout:
			line = line.rstrip()
			if len(line) < 1:
				continue
			if self.dir_pattern.match(line):
				active_dir = line.rstrip(':')
				continue
			album_map[line] = active_dir
		return album_map
			

class MoverController(object):
	" Controller class for the application "
	
	def __init__(self, **args):
		self.config = Configuration(**args)
		self.config.load()
		self.connection_map = {}

	def cleanup(self):
		self.config.save()
		Message.note("Done.")

	def run(self):
		" Run the program "
		while(True):
			opt = Menu.main()
			if opt == 1:
				self._music_sites()
			elif opt == 2:
				# update local directories
				self._update_local()
			else:
				self.cleanup()
				return


	def _music_sites(self):
		" List, Remove, Update music sites "
		if len(self.config['local_music'].get_dir_list()) < 1:
			Message.err("You must have at least one local dir to move music.")
			return False
		while(True):
			action, index = Menu.display_sites(self.config['sites'])
			if action == 'q':
				return
			if action == 'n':
				code, data = Input.site_data()
				if not code:
					continue
				site = RemoteSite(data['name'], data['username'], data['hostname'], data['port'])
				self.config['sites'].append(site)
				continue
			# existing site actions
			if index < 1:
				Message.err("You must specify a site to perform the action on.")
				continue
			index -= 1
			remote_site = self.config['sites'][index]
			if action == 'd':
				if Input.confirm_delete():
					self.config['sites'].pop(index)
			elif action == 'l':
				self._remote_dirs(remote_site)
			elif action == 'b':
				self._remote_blocks(remote_site)
			elif action == 'm':
				if len(remote_site.get_dir_list()) < 1:
					Message.err("Remote sites must have at least 1 dir to move music.")
					continue
				self._move_music(remote_site)


	def _remote_blocks(self, remote_site):
		" Display and remote album blocks from a remote site "
		while(True):
			action, index = Menu.display_blocks(remote_site.blocked_album_list)
			index -= 1
			if action == 'q':
				return
			if action == 'd':
				remote_site.blocked_album_list.pop(index)


	def _remote_dirs(self, remote_site):
		" List remote directories, and delete "
		while(True):
			action, index = Menu.display_remote_list(remote_site.get_dir_list())
			if action == 'q':
				return
			if action == 'd':
				if Input.confirm_delete():
					remote_site.del_dir(index-1)
				continue
			if action == 'a':
				dir = Input.prompt_add_remote_dir()
				remote_site.add_dir(dir)


	def _move_music(self, remote_site):
		" List albums and move music "
		if remote_site not in self.connection_map:
			try:
				self.connection_map[remote_site] = ConnectionManager(remote_site, 
							self.config['local_music'])
			except (SSHException, socket.error), err:
				Message.err("Failed to connect: %s" % (err))
				return
		conn_manager = self.connection_map[remote_site]
		# Refresh the album list for this site 
		album_map, error_list = conn_manager.get_album_list()
		for error in error_list:
			Message.err(error)	
		album_list = album_map.keys()
		album_list.sort()

		# remove blocks
		for block in remote_site.blocked_album_list:
			if block in album_list:
				album_list.remove(block)

		# remove albums already on local
		for album in self.config['local_music'].get_album_cache():
			if album in album_list:
				album_list.remove(album)

		while(True):
			action, index_list = Menu.display_album_list(album_list)
			if action == 'q':
				return
			if action == 'b':
				remove_names = []
				for index in index_list:
					index -= 1
					remote_site.blocked_album_list.append(album_list[index])
					remove_names.append(album_list[index])
				for album in remove_names:
					album_list.remove(album)
				continue
			if action == 'm':
				remove_names = []
				for index in index_list:
					index -= 1
					album_name = album_list[index]
					path = album_map[album_name].rstrip('/') + "/"
					Message.note("Moving %s." % (album_name))
					conn_manager.pull_album(path, album_name)
					remove_names.append(album_name)
				for album in remove_names:
					album_list.remove(album)
				continue
				

	def _update_local(self):
		" Update local directories. "
		while(True):
			action, index = Menu.display_list(self.config['local_music'].get_dir_list(), 	
						self.config['local_music']._active_save_dir+1)
			if action == 's':
				self.config['local_music'].set_save_dir(index-1)
			elif action == 'd':
				if Input.confirm_delete():
					self.config['local_music'].del_dir(index-1)
			elif action == 'a':
				dir = Input.prompt_add_dir()
				if dir:
					self.config['local_music'].add_dir(dir)
			else:
				return



if __name__ == "__main__":
	config_args = {}
	for params in sys.argv[1:]:
		try:
			key, value = params.split('=')
			config_args[key] = value
		except ValueError, err:
			Message.err("Invalid param %s." % (params))

	mover = MoverController(**config_args)
	mover.run()
