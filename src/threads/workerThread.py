'''
Main worker thread for executing pending build jobs.
'''
from time import sleep
import time
import threading
from src.utils import constants
import shutil
from datetime import datetime
import subprocess
import os
import json
import signal
import tarfile
from src.utils import packerUtils




from src.sqlalchemy.db_model import *
from src.sqlalchemy.db_alchemy import db as db_alch


#Todo: The are a LOT of similiar methods in this module. Unify or overload them!

def installFromGalaxy(job, logfile, ansible_roles_path):
	"""Installs Ansible Roles from Ansible Galaxy to the working directory of a build process.

	Args:
		job: A orm job object from database.
		logfile: A file descriptor for the worker logfile.
		ansible_roles_path: The location on where to install the galaxy roles.

	Raises:
		Exception: Ansible Galaxy was not able to install a role.

	"""
	#get all galaxy names from the job db entry.
	galaxyRoles = [mod for mod in job.modules if mod.module_type == 'GALAXY']

	#if there are no galaxy roles to be installed, exit out
	if galaxyRoles.__len__() == 0:
		return

	logfile.write('\nStarted downloading from Galaxy:')
	for role in galaxyRoles:
		try:
			#build the ansible-galaxy command for installing a role into a desired path (here working directory)
			command = 'ansible-galaxy install -f ' + role.name + ' --roles-path=' + ansible_roles_path + ' --ignore-certs'
			#switch to ths folder for easy installation
			os.chdir(ansible_roles_path)
			galaxyOutput = subprocess.check_output(command, shell=True).strip().decode('utf-8')
			#give me all the outputs and put them to the logfile
			logfile.write(galaxyOutput + "\n")
			logfile.flush()
		except Exception as e:
			logfile.write('Could not install role from galaxy: {}'.format(role.name))
			print(e)
			continue



def cp_roles(job, logfile, ansible_roles_path):
	"""Copies Ansible Roles from the locale database to the working directory.

	Args:
		job: A orm job object from database.
		logfile: A file descriptor for logging outputs.
		ansible_roles_path: In which working directory shall these roles be installed?

	Raises:
		Exception: Could not access role, maybe because it is not existent.

	"""
	#get all modules from the job
	roles = [mod for mod in job.modules if mod.module_type == 'Ansible Role']

	#if we dont have any roles to install, exit out.
	if roles.__len__() == 0:
		return

	logfile.write("Copying Ansible Roles:\n")
	for module in roles:
		try:
			#use local ansible-galaxy for installing .tar.gz roles into a desired location.
			filename = str(module.path).split('/')[-1]
			src = constants.ROOT_PATH + '/' + module.path
			#build shell command
			command = 'ansible-galaxy install ' + filename + ' --roles-path=' + ansible_roles_path
			#switch into the working directory
			os.chdir(os.path.dirname(src))
			#call shell command
			galaxyOutput = subprocess.check_output(command, shell=True).strip().decode('utf-8')
			logfile.write(galaxyOutput + "\n")
			logfile.flush()
		except Exception as e:
			logfile.write("Something went wrong with file: " + src + "\tMaybe not existent?\n")
			print(e)
			continue

def cp_rolesForced(logfile, ansible_roles_path):
	"""Copies FORCED Ansible Roles from the locale database to the working directory.

	Args:
		job: A orm job object from database.
		logfile: A file descriptor for logging outputs.
		ansible_roles_path: In which working directory shall these roles be installed?

	Raises:
		Exception: Could not access role, maybe because it is not existent.

	"""
	#get all modules from the job

	forcedRoles = Modules.query.filter_by(isForced = 'true').filter_by(module_type = 'Ansible Role').all()

	#if there are no forced roles, exit out.
	if forcedRoles.__len__() == 0:
		return

	logfile.write("Copying Ansible Roles:\n")
	for module in forcedRoles:
		try:
			#build a shell comand
			filename = str(module.path).split('/')[-1]
			src = constants.ROOT_PATH + '/' + module.path
			command = 'ansible-galaxy install ' + filename + ' --roles-path=' + ansible_roles_path
			#switch to the working directory
			os.chdir(os.path.dirname(src))
			galaxyOutput = subprocess.check_output(command, shell=True).strip().decode('utf-8')
			logfile.write(galaxyOutput + "\n")
			logfile.flush()
		except Exception as e:
			logfile.write("Something went wrong with file: " + src + "\tMaybe not existent?\n")
			print(e)
			continue


def cp_booksAndScripts(job, logfile, directory_trgt, module_type):
	"""Copies Ansible playbooks and bash scripts to the working directory.

	Args:
		job: The targeted job object from database.
		logfile: The logfile of the working directory.
		directory_trgt: Location of the working directory.
		module_type: Is this a Playbook or a Bash Script?

	Raises:
		Exception: Could not access role, maybe because it is not existent.
	"""
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


def cp_booksAndScriptsForced(logfile, directory_trgt):
	"""Copies FORCED Ansible playbooks and bash scripts to the working directory.

	Args:
		logfile: The logfile of the working directory.
		directory_trgt: Location of the working directory.

	Raises:
		Exception: Could not access role, maybe because it is not existent.
	"""
	forcedPlaybooks = Modules.query.filter_by(isForced = 'true').filter_by(module_type = 'Ansible Playbook').all()
	if forcedPlaybooks.__len__() == 0:
		return
	logfile.write('Copying {}'.format('Forced Playbooks'))
	for module in forcedPlaybooks:
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
	"""A thread which is responsibel for building new linux images into openstack.

	Todo:
		Refactor everything into smaller methods.
	"""


	def __init__(self, app, lock):
		"""Initializes a new worker thread.

		Args:
			app: The flask app context.
			lock: A reference to a mutex lock.

		"""

		self.app = app
		self.time = None
		self.lock = lock
		self.p = None
		threading.Thread.__init__(self)

	def run(self):
		print("WorkerThread: Starting working on the pending jobs")
		while 1:
			#flask-sqlalchemy needs the context for some reason
			with self.app.app_context():
				self.time = None
				#try to get the exclusive lock, otherwise wait here
				self.lock.acquire()
				db_alch.session.commit()
				#are there any new jobs which need to be build?
				job = Jobs.query.filter_by(status = 'NEW').first()

				#if there is none, return the lock and go to sleep
				if job is None:
					self.lock.release()
					sleep(5)
					continue

				#set corresponding job from "NEW" to "in_progress"
				job.status = 'in_progress'
				db_alch.session.commit()


				#create tmp folder for this id, if the folder exists, delete it, otherwise create it.
				directoryPath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/'
				if not os.path.exists(directoryPath):
					os.makedirs(directoryPath)
				else:
					shutil.rmtree(directoryPath, ignore_errors=True)
					os.makedirs(directoryPath)

				#create a logfile and fill it with everything we got from the job description
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


				#build directory structures for installation scripts...
				ansible_roles_path = directoryPath + "ansible_roles/"
				os.makedirs(ansible_roles_path)
				ansible_playbooks_path = directoryPath + "ansible_playbooks/"
				os.makedirs(ansible_playbooks_path)
				bash_script_path = directoryPath + "bash_scripts/"
				os.makedirs(bash_script_path)

				#copy all roles into the working directory
				cp_roles(job, logfile, ansible_roles_path)
				cp_rolesForced(logfile, ansible_roles_path)
				logfile.write("\n")

				#copy bash scripts
				cp_booksAndScripts(job, logfile, bash_script_path, 'Bash Script')
				logfile.write("\n")
				cp_booksAndScripts(job, logfile, ansible_playbooks_path, 'Ansible Playbook')
				cp_booksAndScriptsForced(logfile, ansible_playbooks_path)

				#also install galaxy roles into working directory
				installFromGalaxy(job, logfile, ansible_roles_path)
				logfile.write("\n")

				#copy standard ansible.cfg to wirking directory
				fileSrcPath = constants.ROOT_PATH + '/data/config_templates/ansible.cfg'
				shutil.copy2(fileSrcPath, directoryPath + 'ansible.cfg')

				#copy packer.json into ram, for adding new fields like bash scripts or provisioner stuff
				fileSrcPath = constants.ROOT_PATH + '/data/' + 'config_templates/packer.json'
				with open(fileSrcPath) as json_file:
					json_data = json.load(json_file)


				#build a reserved history object in database
				newHistory = History(job.owner, job.name, 'COMMENTARY', None, job.base_image_id, 'false', 'TOBEFILLED')
				db_alch.session.add(newHistory)
				db_alch.session.commit()

				#reobtain history object for getting the new incremented id of the job
				newHistory = History.query.filter_by(name = job.name).first()

				#build the name for the new image
				newOSImageName = 'bibicreator-{}-{}-{}'.format(job.owner, job.name, newHistory.id)
				newHistory.new_image_id = newOSImageName
				db_alch.session.commit()
				#build the packer.json together
				json_data = packerUtils.buildPackerJsonFromConfig(json_data, newOSImageName)

				#obtain and filter all different types of modules for ordering
				bashModules = [mod for mod in job.modules if mod.module_type == 'Bash Script']
				userAnsibleRoles = [mod for mod in job.modules if mod.module_type == 'Ansible Role' and mod.isForced == 'false']
				userAnsiblePlaybooks = [mod for mod in job.modules if mod.module_type == 'Ansible Playbook' and mod.isForced == 'false']


				#get all current forced modules
				forced = Modules.query.filter_by(isForced = 'true').all()
				forcedAnsibleRoles = [mod for mod in forced if mod.module_type == 'Ansible Role' and mod.isForced == 'true']
				forcedAnsiblePlaybooks = [mod for mod in forced if mod.module_type == 'Ansible Playbook' and mod.isForced == 'true']


				galaxyRoles = [mod for mod in job.modules if mod.module_type == 'GALAXY']


				#insert bash scripts into packer.json
				if bashModules.__len__() != 0:
					shellScriptJSONEntry = []
					for module in bashModules:
						shellScriptJSONEntry.append('bash_scripts/' + str(module.path).split('/')[-1])
					#add provisioner to packer json
					addDict = {'type': 'shell', 'scripts': shellScriptJSONEntry}
					json_data['provisioners'].append(addDict)



				#spit the forged packer.json file to working directory
				with open(directoryPath + 'packer.json', 'w+') as outfile:
					json.dump(json_data, outfile)

				######### BUILD MAIN YAML FILE ##########
				#todo export to util class
				mainYaml = open(directoryPath + "main.yaml", "w+")

				#First write in forced roles
				mainYaml.write('---\n\n')
				mainYaml.write('#FORCED ROLES\n')
				mainYaml.write('  - hosts: all\n')
				mainYaml.write('    become: true\n')
				mainYaml.write('    roles:\n')
				for module in forcedAnsibleRoles:
					mainYaml.write("      #" + str(module.name) + "\n")
					mainYaml.write("      - " + str(module.path).split('/')[-1] + "\n")
				mainYaml.write('\n')
				#todo: Refactor this ugly part out
				mainYaml.write('    environment:\n')
				mainYaml.write('      http_proxy: http://proxy.cebitec.uni-bielefeld.de:3128\n')
				mainYaml.write('      https_proxy: http://proxy.cebitec.uni-bielefeld.de:3128\n')
				mainYaml.write('      HTTP_PROXY: http://proxy.cebitec.uni-bielefeld.de:3128\n')
				mainYaml.write('      HTTPS_PROXY: http://proxy.cebitec.uni-bielefeld.de:3128\n')

				#now forced playbooks
				for module in forcedAnsiblePlaybooks:
					mainYaml.write('  #' + str(module.name) + "\n")
					mainYaml.write('  - import_playbook: ansible_playbooks/' + str(module.path).split('/')[-1] + "\n")
				mainYaml.write('\n')


				#now user roles
				mainYaml.write('#USER ROLES\n')
				mainYaml.write('  - hosts: all\n')
				mainYaml.write('    become: true\n')
				mainYaml.write('    roles:\n')
				for module in userAnsibleRoles:
					mainYaml.write("      #" + str(module.name) + "\n")
					mainYaml.write("      - " + str(module.path).split('/')[-1] + "\n")
				for module in galaxyRoles:
					mainYaml.write("      #" + str(module.name) + "\n")
					mainYaml.write("      - " + str(module.name)+ "\n")

				mainYaml.write('\n')
				mainYaml.write('    environment:\n')
				mainYaml.write('      http_proxy: http://proxy.cebitec.uni-bielefeld.de:3128\n')
				mainYaml.write('      https_proxy: http://proxy.cebitec.uni-bielefeld.de:3128\n')
				mainYaml.write('      HTTP_PROXY: http://proxy.cebitec.uni-bielefeld.de:3128\n')
				mainYaml.write('      HTTPS_PROXY: http://proxy.cebitec.uni-bielefeld.de:3128\n')

				mainYaml.write('\n')

				#now user playbooks
				for module in userAnsiblePlaybooks:
					mainYaml.write('  #' + str(module.name) + "\n")
					mainYaml.write('  - import_playbook: ansible_playbooks/' + str(module.path).split('/')[-1] + "\n")
				mainYaml.write('\n')
				mainYaml.close()
				####### FINISHED BUILDING MAIN YAML #########

				#finally switch into working directory and start the packer process.
				logfile.write("\nStarting packer process...\nPacker Output:\n")
				os.chdir(directoryPath)

				try:
					#obtain openstack password from config file into environment variable.
					my_env = os.environ.copy()
					my_env['OS_PASSWORD'] = constants.CONFIG.os_password
					self.time = time.time()

					#startup the packer process
					self.p = subprocess.Popen([constants.CONFIG.packer_path, '-machine-readable', 'build', directoryPath + 'packer.json'], shell=False, stdout=subprocess.PIPE, bufsize=1)
					#restore environment variables and release mutex lock
					os.chdir(constants.ROOT_PATH)
					self.lock.release()
					#p = subprocess.Popen(constants.CONFIG.packer_path+ ' -machine-readable build {}'.format(directoryPath + 'packer.json'), shell=False, stdout=subprocess.PIPE, bufsize=1)

					#tap into standard output of packer for progress data
					for line in iter(self.p.stdout.readline, b''):
						output = line.decode('utf-8')
						#print(output)
						logfile.write(output + '\n')
						logfile.flush()

						#display some progress in db
						splittedPackerOutput = output.split(',')
						print(splittedPackerOutput)
						if splittedPackerOutput[-2] == 'say':
							f_packerOutput = splittedPackerOutput[-1].replace('==>', '').lstrip()
							job.progression = f_packerOutput
						elif splittedPackerOutput[-2] == 'message' and 'TASK' in splittedPackerOutput[-1]:
							f_packerOutput = splittedPackerOutput[-1].replace('*', '').lstrip()
							job.progression = f_packerOutput
						db_alch.session.commit()

					#wait until packer process halts
					self.p.communicate()

					#has packer exited normally?
					if self.p.returncode == 0:
						print('ALL GOD')
					else:
						#if not, clean up everything and set job to failed.
						print('ALL BAD')
						logfile.write("\nFATAL: Packer has failed to build, aborting: \n"  + "\n")
						job.status = 'ABORTED'

						#cleaning up
						for mod in job.modules:
							if mod.module_type == 'GALAXY':
								db_alch.session.delete(mod)

						db_alch.session.commit()

						logfile.flush()
						logfile.close()
						os.remove(directoryPath + 'packer.json')

						# delete tmp modules from galaxy
						for mod in job.modules:
							if mod.module_type == 'GALAXY':
								db_alch.session.delete(mod)

						db_alch.session.delete(newHistory)
						db_alch.session.commit()
						self.p = None
						continue

				except Exception as e:
					self.lock.release()
					print(e)
				#logifle creation has been finished.
				logfile.flush()
				logfile.close()

				#delete away packer.json, because it may contain sensible data
				os.remove(directoryPath + 'packer.json')
				job.status = 'BUILD OKAY'
				db_alch.session.commit()

				###### BUILD HISTORY ######
				#register a new local path for the history object
				historyDirectoryPath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(newHistory.id) + '/'
				if not os.path.exists(historyDirectoryPath):
					os.makedirs(historyDirectoryPath)
				else:
					shutil.rmtree(historyDirectoryPath, ignore_errors=True)
					os.makedirs(historyDirectoryPath)

				#build backup tar
				with tarfile.open(historyDirectoryPath + 'backup.tar.gz', "w:gz") as tar:
					tar.add(directoryPath, arcname=os.path.basename(directoryPath))


				#todo maybe rename for better readability in backup archives
				#cop tmp folder content to history
				for item in os.listdir(directoryPath):
					s = os.path.join(directoryPath, item)
					d = os.path.join(historyDirectoryPath, item)
					if os.path.isdir(s):
						shutil.copytree(s, d, symlinks=False, ignore=None)
					else:
						shutil.copy2(s, d)

				#create NEW database entrys for history modules by copying the original modules
				historyModuleList = []

				#tweak the paths to match the history modules and not the regular system modules
				for mod in job.modules + forced:
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

				#this history is now ready for user inspection
				newHistory.isReady = 'true'
				db_alch.session.commit()
				#everything went fine
				print("Finished building jobid: " + str(job.id))
				sleep(3)

	def shutDownPacker(self):
		"""If the packer process is soft locked, we can try to force shut it down."""
		try:
			#Sometimes packer does not react to one signal.....so spam the shit out of it.
			self.p.send_signal(signal.SIGINT)
			self.p.send_signal(signal.SIGTERM)
			self.p.send_signal(signal.SIGINT)
			self.p.send_signal(signal.SIGTERM)
			self.p.send_signal(signal.SIGINT)
			self.p.send_signal(signal.SIGTERM)


		except Exception as e:
			print('Could not send SIGINT to packer')