'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
'''

"""This module holds all globally available variables."""


ROOT_PATH = ''
TMP_DIRECTORY = '/data/tmp/'
HISTORY_DIRECTORY = '/data/history/'
MODULES_DIRECTORY = '/data/modules/'

SUPPORTED_EXTENSIONS = [('.gz', 'Ansible Role', 'data/modules/ansible_roles'),
						('.yml', 'Ansible Playbook', 'data/modules/ansible_playbooks'),
						('.yaml', 'Ansible Playbook', 'data/modules/ansible_playbooks'),
						('.sh', 'Bash Script', 'data/modules/bash_scripts')]


#gets an overwrite.....obviously...
PACKER_PATH = '/home/awalende/Schreibtisch/packer'

ANSIBLE_STANDARD_CFG = '[defaults]' \
					   'roles_path = ./ansible_roles' \
						'host_key_checking = False'


#Will be set in the startup
CONFIG = None
OS_CONNECTION = None