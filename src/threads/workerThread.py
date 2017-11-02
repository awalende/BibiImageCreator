from time import sleep
import threading
from src.utils import constants
import shutil
import datetime
import subprocess
import os
import json
import tarfile
from src.utils import packerUtils




from src.sqlalchemy.db_model import *
from src.sqlalchemy.db_alchemy import db as db_alch






'''
Main worker thread for executing pending build jobs.
'''


def installFromGalaxy(job, logfile, ansible_roles_path):
	#get all galaxy names
	galaxyRoles = [mod for mod in job.modules if mod.module_type == 'GALAXY']

	if galaxyRoles.__len__() == 0:
		return

	logfile.write('\nStarted downloading from Galaxy:')
	for role in galaxyRoles:
		try:
			command = 'ansible-galaxy install ' + role.name + ' --roles-path=' + ansible_roles_path + ' --ignore-certs'
			galaxyOutput = subprocess.check_output(command, shell=True).strip().decode('utf-8')
			logfile.write(galaxyOutput + "\n")
			logfile.flush()
		except Exception as e:
			logfile.write('Could not install role from galaxy: {}'.format(role.name))
			print(e)
			continue



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



class JobWorker(threading.Thread):

	def __init__(self, app):

		self.app = app
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


				#create tmp folder for this id, if the folder exists, delete it, otherwise create
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

				#also install galaxy roles
				installFromGalaxy(job, logfile, ansible_roles_path)


				logfile.write("\n")

				job.progress = 'build config'
				db_alch.session.commit()


				#copy ansible.cfg
				fileSrcPath = constants.ROOT_PATH + '/data/config_templates/ansible.cfg'
				shutil.copy2(fileSrcPath, directoryPath + 'ansible.cfg')

				#copy packer.json into ram, for adding new fields like bash scripts or provisioner stuff
				fileSrcPath = constants.ROOT_PATH + '/data/' + 'config_templates/packer.json'
				with open(fileSrcPath) as json_file:
					json_data = json.load(json_file)


				#build it for our environment
				newOSImageName = 'bibicreator-{}-{}-{}'.format(job.owner, job.name, job.id)
				json_data = packerUtils.buildPackerJsonFromConfig(json_data, newOSImageName)




				#obtain and filter all different types of modules for ordering
				bashModules = [mod for mod in job.modules if mod.module_type == 'Bash Script']
				userAnsibleRoles = [mod for mod in job.modules if mod.module_type == 'Ansible Role' and mod.isForced == 'false']
				userAnsiblePlaybooks = [mod for mod in job.modules if mod.module_type == 'Ansible Playbook' and mod.isForced == 'false']
				forcedAnsibleRoles = [mod for mod in job.modules if mod.module_type == 'Ansible Role' and mod.isForced == 'true']
				forcedAnsiblePlaybooks = [mod for mod in job.modules if mod.module_type == 'Ansible Playbook' and mod.isForced == 'true']
				galaxyRoles = [mod for mod in job.modules if mod.module_type == 'GALAXY']


				#insert bash scripts into packer.json
				if bashModules.__len__() != 0:
					shellScriptJSONEntry = []
					for module in bashModules:
						shellScriptJSONEntry.append('bash_scripts/' + str(module.path).split('/')[-1])
					#add provisioner to packer json
					addDict = {'type': 'shell', 'script': shellScriptJSONEntry}
					json_data['provisioners'].append(addDict)



				#spit the forged packer.json file to disk
				with open(directoryPath + 'packer.json', 'w+') as outfile:
					json.dump(json_data, outfile)

				#build main.yml
				#todo export to util class



				mainYaml = open(directoryPath + "main.yaml", "w+")


				#First push in forced roles
				mainYaml.write('---\n\n')
				mainYaml.write('#FORCED ROLES\n')
				mainYaml.write('  - hosts: all\n')
				mainYaml.write('    roles:\n')
				for module in forcedAnsibleRoles:
					mainYaml.write("      - " + str(module.path).split('/')[-1] + "\n")
				mainYaml.write('\n')

				#now forced playbooks
				for module in forcedAnsiblePlaybooks:
					mainYaml.write('  - import_playbook: ansible_playbooks/' + str(module.path).split('/')[-1] + "\n")

				mainYaml.write('\n')


				#now user roles
				mainYaml.write('#USER ROLES\n')
				mainYaml.write('  - hosts: all\n')
				mainYaml.write('    roles:\n')
				for module in userAnsibleRoles:
					mainYaml.write("      - " + str(module.path).split('/')[-1] + "\n")
				for module in galaxyRoles:
					mainYaml.write("      - " + str(module.name)+ "\n")

				mainYaml.write('\n')

				#now user playbooks
				for module in userAnsiblePlaybooks:
					mainYaml.write('  - import_playbook: ansible_playbooks/' + str(module.path).split('/')[-1] + "\n")
				mainYaml.write('\n')

				mainYaml.close()

				logfile.write("\nStarting packer process...\nPacker Output:\n")

				job.progress = 'running packer'
				db_alch.session.commit()

				os.chdir(directoryPath)

				try:
					my_env = os.environ.copy()
					my_env['OS_PASSWORD'] = constants.CONFIG.os_password


					p = subprocess.Popen(constants.CONFIG.packer_path+ ' -machine-readable build packer.json', shell=True, stdout=subprocess.PIPE, bufsize=1)
					for line in iter(p.stdout.readline, b''):
						output = line.decode('utf-8')
						print(output)
						logfile.write(output + '\n')
					#p.stdout.close()
					p.communicate()

					if p.returncode == 0:
						print('ALL GOD')
					else:
						print('ALL BAD')
						logfile.write("\nFATAL: Packer has failed to build, aborting: \n"  + "\n")

						job.status = 'ABORTED'
						job.progress = 'stopped'

						for mod in job.modules:
							if mod.module_type == 'GALAXY':
								db_alch.session.delete(mod)

						db_alch.session.commit()

						logfile.flush()
						logfile.close()
						os.remove(directoryPath + 'packer.json')
						continue

				except Exception as e:
					print(e.output)

				#logfile.write(packerOutput + "\n")
				logfile.flush()
				logfile.close()

				os.remove(directoryPath + 'packer.json')

				job.status = 'BUILD OKAY'
				job.progress = 'finished'
				db_alch.session.commit()


				#build history and structure
				newHistory = History(job.owner, job.name, 'COMMENTARY', None, job.base_image_id, 'TOBEFILLED')
				db_alch.session.add(newHistory)
				db_alch.session.commit()

				#reobtain history object
				newHistory = History.query.filter_by(name = job.name).first()



				historyDirectoryPath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(newHistory.id) + '/'
				if not os.path.exists(historyDirectoryPath):
					os.makedirs(historyDirectoryPath)
				else:
					shutil.rmtree(historyDirectoryPath, ignore_errors=True)
					os.makedirs(historyDirectoryPath)

				#build backup tar
				with tarfile.open('backup.tar.gz', "w:gz") as tar:

					tar.add(directoryPath, arcname=os.path.basename(directoryPath))


				#todo maybe rename for better readability in backup archives
				#cop tmp content to history
				for item in os.listdir(directoryPath):
					s = os.path.join(directoryPath, item)
					d = os.path.join(historyDirectoryPath, item)
					if os.path.isdir(s):
						shutil.copytree(s, d, symlinks=False, ignore=None)
					else:
						shutil.copy2(s, d)

				#create NEW database entrys for history modules by copying the original modules
				#todo remember galaxy list
				historyModuleList = []
				for mod in job.modules:
					if mod.module_type == 'Ansible Role':
						modulePath = '/data/history/' + str(newHistory.id) + '/ansible_roles/' + str(mod.path).split('/')[-1]
					elif mod.module_type == 'Ansible Playbook':
						modulePath = '/data/history/' + str(newHistory.id) + '/ansible_playbooks/' + \
									 str(mod.path).split('/')[-1]
					else:
						modulePath = '/data/history/' + str(newHistory.id) + '/bash_scripts/' + \
									 str(mod.path).split('/')[-1]
					historyModuleList.append(HistoryModules(mod.name, mod.owner, mod.description, mod.version, mod.module_type, modulePath, mod.isForced))
					db_alch.session.add(historyModuleList[-1])
				db_alch.session.commit()

				#add to relation
				for mod in historyModuleList:
					newMod = HistoryModules.query.filter_by(id = mod.id).first()
					newHistory.modules.append(newMod)


				#delete tmp modules from galaxy
				for mod in job.modules:
					if mod.module_type == 'GALAXY':
						db_alch.session.delete(mod)
				db_alch.session.commit()



				print("Finished building jobid: " + str(job.id))



				sleep(3)