'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
	-------------------------------------------------
	config.py
	This file is including the parser for the configuration file
	located in /etc/bibicreator/config.ini.
	It also checks if all needed fields in the file are set.
'''


import sys


config = None
class Configuration:
	'''Class for parsing an .ini file. Also checks needed Fields.'''

	def __init__(self, parsedINI):
		'''Transform a .ini file into a configuration for usage in all BibiCreator modules.'''
		try:
			#DATABASE FIELDS
			self.db_user = parsedINI['database']['db_user']
			self.db_password = parsedINI['database']['db_password']
			self.db_url = parsedINI['database']['db_url']

			#OPENSTACK FIELDS
			self.os_auth_url = parsedINI['openstack']['os_auth_url']
			self.os_user = parsedINI['openstack']['os_user']
			self.os_password = parsedINI['openstack']['os_password']
			self.os_project_name = parsedINI['openstack']['os_project_name']
			self.os_user_domain_id = parsedINI['openstack']['os_user_domain_id']
			self.os_project_domain_name = parsedINI['openstack']['os_project_domain_name']
			self.os_availability_zone = parsedINI['openstack']['os_availability_zone']
			self.os_base_img_id = parsedINI['openstack']['os_base_img_id']

			#ADMIN DATA FIELDS
			self.admin_password = parsedINI['admin']['admin_password']
			self.admin_email = parsedINI['admin']['admin_email']

			#PACKER FIELDS
			self.os_flavor = parsedINI['openstack']['os_flavor']
			self.os_ssh_username = parsedINI['openstack']['os_ssh_username']
			self.os_network = parsedINI['openstack']['os_network']
			self.packer_path = parsedINI['misc']['packer_path']

		except KeyError as e:
			print('Could not find entry in config file: {}'.format(e))
			sys.exit(-1)


		#misc. These fields are optional.
		if not 'auto_backup' in parsedINI['misc']:
			self.auto_backup = False
		else:
			if parsedINI['misc']['auto_backup'] == 'yes':
				self.auto_backup = True
			else:
				self.auto_backup = False