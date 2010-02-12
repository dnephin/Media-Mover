"""
 Models for Music Mover.
"""

import os
from stat import ST_MODE, S_ISDIR


class MusicSite(object):
	" Base object model for music host "	
	def __init__(self):
		self._dir_list = []

	def add_dir(self, dir):
		self._dir_list.append(dir)
		self.refresh_album_cache()

	def del_dir(self, index):
		self._dir_list.pop(index)
		self.refresh_album_cache()

	def get_dir_list(self):
		return self._dir_list

	def refresh_album_cache(self):
		return

class LocalMusic(MusicSite):
	" a local music site "

	max_recurse = 3

	def __init__(self):
		self._active_save_dir = 0
		self._album_cache = []
		self.recurse_count = 0
		super(LocalMusic, self).__init__()

	def set_save_dir(self, index):
		if index > -1 and index < len(self._dir_list):
			self._active_save_dir = index

	def get_save_dir(self):
		if self._active_save_dir > len(self._dir_list):
			self._active_save_dir = 0
		return self._dir_list[self._active_save_dir]

	def get_album_cache(self):
		return self._album_cache

	def clear_album_cache(self):
		self._album_cache = []
		
	def refresh_album_cache(self):
		" Build the list of albums. "
		self.clear_album_cache()
		for dir in self._dir_list:
			album_list = self._search_dir_for_album(dir)
			self._album_cache.extend(album_list)

	def _search_dir_for_album(self, dir):
		if self.recurse_count >= LocalMusic.max_recurse:
			return []
		dir_list = []
		try:
			for album_dir in os.listdir(dir):
				full_dir = os.path.join(dir, album_dir)
				if not S_ISDIR(os.stat(full_dir)[ST_MODE]):
					continue
				dir_list.append(album_dir)
				self.recurse_count += 1
				dir_list.extend(self._search_dir_for_album(full_dir))
				self.recurse_count -= 1
			return dir_list
		except OSError, err:
			# TODO: log error
			return []


class RemoteSite(MusicSite):
	" Model for remote sites "

	def __init__(self, name, username, hostname, port):
		self.hostname = hostname
		self.port = port
		self.name = name
		self.username = username
		self.blocked_album_list = []
		super(RemoteSite, self).__init__()


