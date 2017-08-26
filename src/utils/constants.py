ROOT_PATH = ''
TMP_DIRECTORY = '/data/tmp/'
SUPPORTED_EXTENSIONS = [('.gz', 'Ansible Role', 'data/modules/ansible_roles'),
						('.yml', 'Ansible Playbook', 'data/modules/ansible_playbooks'),
						('.yaml', 'Ansible Playbook', 'data/modules/ansible_playbooks'),
						('.sh', 'Bash Script', 'data/modules/bash_scripts')]

#todo this is hardcoded aswell -.-
PACKER_PATH = '/home/awalende/Schreibtisch/packer'

ANSIBLE_STANDARD_CFG = '[defaults]' \
					   'roles_path = ./ansible_roles' \
						'host_key_checking = False'