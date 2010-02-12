"""
 User input and display class for MusicMover.
"""

import os
import math
import getpass
from stat import S_ISDIR, ST_MODE


class Color(object):
	" Colorize output "
	wrap = '\033[%sm'

	red =    '0;31'
	green =  '0;32'
	yellow = '1;33'
	blue =   '0;34'
	lblue =  '1;34'
	lred =   '1;31'
	white =  '1;37'
	lgray =  '0;37'

	color_on = True

	@staticmethod
	def make(color, str):
		if not Color.color_on:
			return str
		return Color.wrap % (color) + str + Color.wrap % ('')


class Input(object):
	" Accept and validate user input "
	# TODO: handle EOF from raw_input in all input methods

	@staticmethod
	def action_input(item_list, action_list, min_option=1):
		" Get the input, and make sure it is in range "
		while(True):
			action = raw_input(Color.make(Color.blue, "Enter Action: "))
			values = action.split()
			if values[0] not in action_list:
				print Color.make(Color.lred, "Invalid action %s (try %s)" % (values[0], action_list))
				continue
			if len(values) < 2:
				return values[0], min_option-1
			try:
				option = int(values[1])
			except ValueError, err:
				print Color.make(Color.lred, "Not a number %s." % (values[1]))
				continue
			if option < min_option or option > len(item_list)-1:
				print Color.make(Color.lred, "Selection out of range (%d - %d)." % (min_option, len(item_list)-1))
				continue
			return (values[0], option)

	@staticmethod
	def action_list_input(item_list, action_list):
		while(True):
			action = raw_input(Color.make(Color.blue, "Enter Action: "))
			values = action.split()
			if values[0] not in action_list:
				print Color.make(Color.lred, "Invalid action %s (try %s)" % (values[0], action_list))
				continue
			if len(values) < 2:
				return values[0], []

			index_list = []
			# split up sections
			for index_range in values[1].split(','):
				if '-' not in index_range:
					# parse singles
					try:
						option = int(index_range)
						index_list.append(option)
					except ValueError, err:
						print Color.make(Color.lred, "Not a number %s." % (index_range))
						break
				else:
					# parse ranges
					try:
						min, max = map(int, index_range.split('-'))
						index_list.extend(range(min, max+1))
					except ValueError, err:
						print Color.make(Color.lred, "Invalid range, or not a number %s." % (err))
						break
			else:
				for index in index_list:
					if index < 1 or index > len(item_list)-1:
						print Color.make(Color.lred, "Selection (%d) out of range (%d - %d)." % (index, 1, len(item_list)-1))
						break
				else:
					return values[0], index_list
	
		
	@staticmethod
	def menu_input(item_list, min_option=1):
		" Get the input, and make sure it is in range "
		while(True):
			option = raw_input(Color.make(Color.blue, "Enter Selection: "))
			try:
				option = int(option)
			except ValueError, err:
				print Color.make(Color.lred, "Not a number.")
				continue
			if option < min_option or option > len(item_list)-1:
				print Color.make(Color.lred, 
						"Selection out of range (%d - %d)." % (min_option, len(item_list)-1))
				continue
			return option


	@staticmethod
	def prompt_add_dir():
		dir = raw_input(Color.make(Color.blue, "Directory name: "))
		try:
			if S_ISDIR(os.stat(dir)[ST_MODE]):
				return dir
		except OSError:
			pass
		print Color.make(Color.lred, "Invalid Directory. Could not add.")
		return None


	@staticmethod
	def prompt_add_remote_dir():
		return raw_input(Color.make(Color.blue, "Directory name: "))


	@staticmethod
	def site_data():
		data = {}
		data['name'] = raw_input(Color.make(Color.blue, "Enter the name of the site: "))
		data['username'] = os.getlogin()
		username = raw_input(Color.make(Color.blue, "Enter the username for the site [%s]: " % (data['username'])))
		if len(username) > 0:
			data['username'] = username
		data['hostname'] = raw_input(Color.make(Color.blue, "Enter the hostname of the site: "))
		while(True):
			port = raw_input(Color.make(Color.blue, "Enter the port of the site [22]: "))
			if len(port) == 0:
				data['port'] = 22
				break
			try:
				data['port'] = int(port)
			except ValueError, err:
				print Color.make(Color.lred, "Not a number.")
				continue
			break
		return (True, data)

	@staticmethod
	def prompt_pass():
		return getpass.getpass(Color.make(Color.lblue, "Password: "))
		

	@staticmethod
	def confirm_delete():
		while(True):
			resp = raw_input(Color.make(Color.red, "Are you sure you want to delete? [y/n]: ")).lower()
			if resp not in ['y', 'n']:
				print Color.make(Color.lred, "Invalid response.")
				continue
			if resp == 'y':
				return True
			return False


class Menu(object):
	" Display Menu to the user "

	split_size = 50

	@staticmethod
	def _display_menu(item_list, star_index=-1):
		" Dislay the list as a menu, the first item is the title "
		# title
		text = "\n    [```  %s  ```]  " % (item_list[0])
		print Color.make(Color.yellow, text + ". " * ((80-len(text))/2))

		list_size = len(item_list)-1
		split_at = int(math.ceil(list_size/2.0))
		single_line = "%3d. %s"
		double_line = "%3d. %-50s   %3d. %-50s"
	
		# entries
		if list_size <= Menu.split_size:
			# single column
			for i in range(1,list_size+1):
				line = single_line % (i, item_list[i])
				if i == star_index:
					print Color.make(Color.white, " *" + line)
					continue
				print Color.make(Color.lgray, "  " + line)
		else:
			# two columns
			for i in range(1, split_at+1):
				if i == split_at and list_size % 2 == 1:
					# last line
					line = single_line % (i, item_list[i])
				else:
					line = double_line % (i, item_list[i][:49], i+split_at, item_list[i+split_at][:49])
				print Color.make(Color.lgray, "  " + line)

		# footer
		print Color.make(Color.yellow, " " * 4 + ". " * 38)

	@staticmethod
	def main():
		" Display main menu, and return validated input. "

		menu = [
			'Main Menu',
			'Remote Sites menu (Move music)',
			'Local music menu',
			'Exit'
		]
		Menu._display_menu(menu)
		return Input.menu_input(menu)

	@staticmethod
	def display_list(list, active_dir):
		if len(list) == 0:
			menu = ["No directories in list"]
		else:
			menu = ['Directory List']
			menu.extend(list)
		Menu._display_menu(menu, star_index=active_dir)
		print Color.make(Color.lblue, "Active save directory marked with a * ")
		print Color.make(Color.lblue, "Enter the action (a: add new, d: delete, s: set active) or q to return.")
		return Input.action_input(menu, ['a', 'd', 's', 'q'])

	@staticmethod
	def display_remote_list(list):
		if len(list) == 0:
			menu = ["No directories in list"]
		else:
			menu = ['Remote Directory List']
			menu.extend(list)
		Menu._display_menu(menu)
		print Color.make(Color.lblue, "Enter the action (d: delete, a: add) or q to return.")
		return Input.action_input(menu, ['d', 'a', 'q'])
		

	@staticmethod
	def display_sites(sites):
		if len(sites) == 0:
			menu = ["No sites."]
		else:
			menu = ['Sites List']
			# TODO: fixed width for username+hostname+port
			for site in sites:
				menu.append("%-15s (%s@%s:%s)\t[%d dirs] [%d blocks]" % (site.name, site.username,
						site.hostname, site.port, len(site.get_dir_list()), len(site.blocked_album_list)))
		Menu._display_menu(menu)
		print Color.make(Color.lblue, "Enter the action (n: new site, m: move music, "
					"d: del site, l: dir menu, b: block menu), or q to return.")
		return Input.action_input(menu, ['n', 'd', 'm', 'l', 'b', 'q'])
		

	@staticmethod
	def display_album_list(album_list):
		if len(album_list) == 0:
			menu = ["No albums."]
		else:
			menu = ['Album List']
			menu.extend(album_list)
		Menu._display_menu(menu)
		print Color.make(Color.lblue, "Enter the action (b: block, m: move) [ex: m 1,3-5] or q to return.")
		return Input.action_list_input(menu, ['b','m','q'])

	
	@staticmethod
	def display_blocks(block_list):
		if len(block_list) == 0:
			menu = ["No blocks."]
		else:
			menu = ["Blocked Album List"]
			menu.extend(block_list)
		Menu._display_menu(menu)
		print Color.make(Color.lblue, "Enter the action (d: delete block) or q to return.")
		return Input.action_input(menu, ['d', 'q'])


class Message(object):
	" Display error or notification messages "

	@staticmethod
	def err(msg):
		print Color.make(Color.lred, msg)

	@staticmethod
	def note(msg):
		print Color.make(Color.lblue, msg)


