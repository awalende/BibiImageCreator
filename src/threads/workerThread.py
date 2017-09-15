from time import sleep
from src.utils import db_connector
import threading
import os
from src.utils import constants
import shutil
import datetime
import subprocess
import os
import json
from flask import Blueprint



from src.sqlalchemy.db_model import *
from src.sqlalchemy.db_alchemy import db as db_alch






'''
Main worker thread for executing pending build jobs.
'''

def cp_roles(job, logfile, ansible_roles_path):
	#get all modules from the job
	roles = [mod for mod in job.modules if mod.module_type == 'Ansible Role']

	if roles.__len__() == 0:
		return

	logfile.write("Copying Ansible Roles:\n")
	for module in roles:
		try:
			filename = str(module.path).split('/')[-1]
			src = constants.ROOT_PATH + '/' + module.path
			command = 'ansible-galaxy install ' + filename + ' --roles-path=' + ansible_roles_path
			os.chdir(os.path.dirname(src))
			galaxyOutput = subprocess.check_output(command, shell=True).strip().decode('utf-8')
			logfile.write(galaxyOutput + "\n")
			logfile.flush()
		except Exception as e:
			logfile.write("Something went wrong with file: " + src + "\tMaybe not existent?\n")
			print(e)
			continue


def cp_booksAndScripts(job, logfile, directory_trgt, module_type):
	modules = [mod for mod in job.modules if mod.module_type == module_type]

	print(modules)

	if modules.__len__() == 0:
		return

	logfile.write('Copying {}'.format(module_type))
	for module in modules:
		try:
			filename = str(module.path).split('/')[-1]
			src = constants.ROOT_PATH + '/' + module.path
			dst = directory_trgt + filename
			shutil.copy2(src, dst)
			logfile.write("Copying from " + src + " to target " + dst + "\n")
		except Exception as e:
			logfile.write("Something went wrong with file: " + src + "\tMaybe not existent?\n")
			continue
		else:
			pass




def copyPlaybooksAndScripts(queryResult, directoryPath, target_path, logfile):
	if queryResult.__len__() != 0:
		for sqlRow in queryResult:
			try:
				filename = str(sqlRow[1]).split('/')[-1]
				src = constants.ROOT_PATH + '/' + str(sqlRow[1])
				dst = directoryPath + target_path + filename
				shutil.copy2(src, dst)
				logfile.write("Copying from " + src + " to target " + dst + "\n")
			except Exception as e:
				logfile.write("Something went wrong with file: " + src + "\tMaybe not existent?\n")
				continue
			else:
				pass


class JobWorker(threading.Thread):

	def __init__(self, app):

		self.app = app

		#self.db_credentials = db_credentials
		#self.db = db_connector.DB_Connector(*self.db_credentials)
		threading.Thread.__init__(self)


	def run(self):
		#todo What if framework crashes and there were running threads? Cleanup after x minutes? Force abort?


		print("WorkerThread: Starting working on the pending jobs")
		while 1:
			#flask-sqlalchemy needs the context
			with self.app.app_context():

				job = Jobs.query.filter_by(status = 'NEW').first()

				if job is None:
					sleep(5)
					continue

				#set corresponding job from "NEW" to "in_progress"
				job.status = 'in_progress'
				db_alch.session.commit()


				#create tmp folder for this id
				directoryPath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/'
				if not os.path.exists(directoryPath):
					os.makedirs(directoryPath)
				else:
					shutil.rmtree(directoryPath, ignore_errors=True)
					os.makedirs(directoryPath)

				#create a logfile and fill it with everything we got
				logfile = open(directoryPath + "log.txt", "w+")
				logfile.write("********\n")
				logfile.write("LOGFILE FOR JOB " + str(job.id) + " Name: " + str(job.name) + "\n")
				logfile.write("********\n\n")
				logfile.write("Created by: " + str(job.owner) + "\n")
				logfile.write("Job created on: " + str(job.date) + "\n")
				logfile.write("Job processed on: " + str(datetime.now())+ "\n\n")
				logfile.write("TMP Directory: " + str(directoryPath) + "\n")
				logfile.write("OpenStack Base Image ID: " + str(job.base_image_id) + "\n")
				logfile.write("********\n\nGathering Roles, Playbooks, Scripts to this tmp directory...\n\n")


				#jobx.progress = 'gathering'
				#db_alch.session.commit()




				#build directory structure
				ansible_roles_path = directoryPath + "ansible_roles/"
				os.makedirs(ansible_roles_path)

				ansible_playbooks_path = directoryPath + "ansible_playbooks/"
				os.makedirs(ansible_playbooks_path)

				bash_script_path = directoryPath + "bash_scripts/"
				os.makedirs(bash_script_path)


				#Copy Roles to tmp
				job.progress = 'copying modules'
				db_alch.session.commit()


				cp_roles(job, logfile, ansible_roles_path)


				logfile.write("\n")

				#copy bash scripts
				cp_booksAndScripts(job, logfile, bash_script_path, 'Bash Script')
				logfile.write("\n")


				#"install roles"
				cp_booksAndScripts(job, logfile, ansible_playbooks_path, 'Ansible Playbook')


				logfile.write("\n")

				job.progress = 'build config'
				db_alch.session.commit()


				#copy ansible.cfg
				configSrc = constants.ROOT_PATH + '/data/config_templates/ansible.cfg'
				shutil.copy2(configSrc, directoryPath + 'ansible.cfg')

				#copy packer.json
				configSrc = constants.ROOT_PATH + '/data/' + 'config_templates/packer.json'
				with open(configSrc) as json_file:
					json_data = json.load(json_file)

				#obtain all different types of modules for ordering
				bashModules = [mod for mod in job.modules if mod.module_type == 'Bash Script']
				userAnsibleRoles = [mod for mod in job.modules if mod.module_type == 'Ansible Role' and mod.isForced == 'false']
				userAnsiblePlaybooks = [mod for mod in job.modules if mod.module_type == 'Ansible Playbook' and mod.isForced == 'false']
				forcedAnsibleRoles = [mod for mod in job.modules if mod.module_type == 'Ansible Role' and mod.isForced == 'true']
				forcedAnsiblePlaybooks = [mod for mod in job.modules if mod.module_type == 'Ansible Playbook' and mod.isForced == 'true']

				#insert bash scripts into packer.json
				if bashModules.__len__() != 0:
					shellScriptJSONEntry = []
					for module in bashModules:
						shellScriptJSONEntry.append('bash_scripts/' + str(module.path).split('/')[-1])
					#add provisioner to packer json
					addDict = {'type': 'shell', 'script': shellScriptJSONEntry}
					json_data['provisioners'].append(addDict)

				#todo remove after debugging
				pythonAptProvisioner = {'type': 'shell', 'inline': ['sleep 1', 'apt-get update', 'apt-get install -y python']}
				json_data['provisioners'].insert(0, pythonAptProvisioner)

				with open(directoryPath + 'packer.json', 'w+') as outfile:
					json.dump(json_data, outfile)

				#build main.yml
				#todo export to util class
				mainYaml = open(directoryPath + "main.yaml", "w+")
				mainYaml.write('---\n\n')
				mainYaml.write('  - hosts: all\n')
				mainYaml.write('    tasks:\n')

				#first add forced playbooks
				for module in forcedAnsiblePlaybooks:
					mainYaml.write("      - include: ansible_playbooks/" + str(module.path).split('/')[-1] + "\n")
					mainYaml.write("        ignore_errors: yes\n")

				#add user playbooks
				for module in userAnsiblePlaybooks:
					mainYaml.write("      - include: ansible_playbooks/" + str(module.path).split('/')[-1] + "\n")
					mainYaml.write("        ignore_errors: yes\n")

				mainYaml.write("\n")

				#add all roles
				if forcedAnsibleRoles.__len__() != 0 or userAnsibleRoles.__len__() != 0:
					mainYaml.write("    roles:\n")
					for module in forcedAnsibleRoles:
						mainYaml.write("      - " + str(module.path).split('/')[-1] + "\n")
					for module in userAnsibleRoles:
						mainYaml.write("      - " + str(module.path).split('/')[-1] + "\n")
				mainYaml.close()

				logfile.write("\nStarting packer process...\nPacker Output:\n")

				job.progress = 'running packer'
				db_alch.session.commit()

				os.chdir(directoryPath)

				try:
					packerOutput = subprocess.check_output(constants.PACKER_PATH + ' build packer.json',
														   shell=True).strip().decode('utf-8')
				except Exception as e:
					print(e)
					logfile.write("\nFATAL: Packer has failed to build, aborting: \n" + str(e) + "\n")

					job.status = 'ABORTED'
					job.progress = 'stopped'

					db_alch.session.commit()

					logfile.flush()
					logfile.close()
					continue
				logfile.write(packerOutput + "\n")
				logfile.flush()
				logfile.close()

				job.status = 'BUILD OKAY'
				job.progress = 'finished'
				db_alch.session.commit()

				print("Finished building jobid: " + str(job.id))



				sleep(3)