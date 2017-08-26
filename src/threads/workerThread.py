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

'''
Main worker thread for executing pending build jobs.
'''
def copyRoles(queryResult, ansible_roles_path, logfile):
	if queryResult.__len__() != 0:
		logfile.write("Copying Ansible Roles:\n")
		for sqlRow in queryResult:
			try:
				filename = str(sqlRow[1]).split('/')[-1]
				src = constants.ROOT_PATH + '/' + str(sqlRow[1])
				command = 'ansible-galaxy install ' + filename + ' --roles-path=' + ansible_roles_path
				os.chdir(os.path.dirname(src))
				galaxyOutput = subprocess.check_output(command, shell=True).strip().decode('utf-8')
				logfile.write(galaxyOutput + "\n")
			except Exception as e:
				logfile.write("Something went wrong with file: " + src + "\tMaybe not existent?\n")
				print(e)
				continue

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

	def __init__(self, db_credentials):

		self.db_credentials = db_credentials
		self.db = db_connector.DB_Connector(*self.db_credentials)
		threading.Thread.__init__(self)

	def run(self):

		print("WorkerThread: Starting working on the pending jobs")
		while 1:
			queryResult = ()
			#check if there are any new jobs
			try:
				queryResult = self.db.queryAndResult("SELECT id, status, name, owner, base_image_id, date FROM Jobs", None)
			except Exception as e:
				print("There was a problem connecting to the db:")
				print(e)
				continue
			#if there are no jobs, go to sleep
			if queryResult.__len__() == 0:
				sleep(5)
				continue
			#take the first result and work it off
			jobID = queryResult[0][0]

			#set corresponding job from "NEW" to "in_progress"
			#queryResult = self.db.queryAndResult("UPDATE Jobs SET status = %s WHERE Jobs.id = %s", ('in_progress', jobID))
			#self.db.db.commit()

			#create tmp folder for this id
			directoryPath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(jobID) + '/'
			if not os.path.exists(directoryPath):
				os.makedirs(directoryPath)
			else:
				shutil.rmtree(directoryPath, ignore_errors=True)
				os.makedirs(directoryPath)

			#create a logfile and fill it with everything we got
			logfile = open(directoryPath + "log.txt", "w+")
			logfile.write("********\n")
			logfile.write("LOGFILE FOR JOB " + str(queryResult[0][0]) + " Name: " + str(queryResult[0][2]) + "\n")
			logfile.write("********\n\n")
			logfile.write("Created by: " + str(queryResult[0][3]) + "\n")
			logfile.write("Job created on: " + str(queryResult[0][5]) + "\n")
			logfile.write("Job processed on: " + str(datetime.datetime.now())+ "\n\n")
			logfile.write("TMP Directory: " + str(directoryPath) + "\n")
			logfile.write("OpenStack Base Image ID: " + str(queryResult[0][4]) + "\n")
			logfile.write("********\n\nGathering Roles, Playbooks, Scripts to this tmp directory...\n\n")

			#todo update job entry progress to gather


			#build directory structure
			ansible_roles_path = directoryPath + "ansible_roles/"
			os.makedirs(ansible_roles_path)

			ansible_playbooks_path = directoryPath + "ansible_playbooks/"
			os.makedirs(ansible_playbooks_path)

			bash_script_path = directoryPath + "bash_scripts/"
			os.makedirs(bash_script_path)


			#Copy Roles to tmp
			#todo: factor out to method

			ansiblePlaysQuery = self.db.queryAndResult("SELECT id, path FROM Modules JOIN jobs_modules WHERE module_type = %s AND Modules.id = jobs_modules.id_modules AND jobs_modules.id_jobs = %s", ('Ansible Playbook', queryResult[0][0]))
			copyPlaybooksAndScripts(ansiblePlaysQuery, directoryPath, 'ansible_playbooks/', logfile)

			logfile.write("\n")

			#copy bash scripts
			bashScriptQuery = self.db.queryAndResult("SELECT id, path FROM Modules JOIN jobs_modules WHERE module_type = %s AND Modules.id = jobs_modules.id_modules AND jobs_modules.id_jobs = %s", ('Bash Script', queryResult[0][0]))
			copyPlaybooksAndScripts(bashScriptQuery, directoryPath, 'bash_scripts/', logfile)
			logfile.write("\n")


			#"install roles"
			ansibleRolesQuery = self.db.queryAndResult("SELECT id, path FROM Modules JOIN jobs_modules WHERE module_type = %s AND Modules.id = jobs_modules.id_modules AND jobs_modules.id_jobs = %s", ('Ansible Role', queryResult[0][0]))
			copyRoles(ansibleRolesQuery, ansible_roles_path, logfile)


			logfile.write("\n")

			#now add forced modules
			forcedAnsibleRolesQuery = self.db.queryAndResult("SELECT id, path FROM Modules WHERE isForced = %s AND module_type = %s", ('True', 'Ansible Role'))
			copyRoles(forcedAnsibleRolesQuery, ansible_roles_path, logfile)

			#forced playbooks
			forcedAnsiblePlaybooksQuery = self.db.queryAndResult("SELECT id, path FROM Modules WHERE isForced = %s AND module_type = %s", ('True', 'Ansible Playbook'))
			copyPlaybooksAndScripts(forcedAnsiblePlaybooksQuery, directoryPath, 'ansible_playbooks/', logfile)

			#forced scripts
			forcedScriptsQuery = self.db.queryAndResult("SELECT id, path FROM Modules WHERE isForced = %s AND module_type = %s", ('True', 'Bash Script'))
			copyPlaybooksAndScripts(forcedScriptsQuery, directoryPath, 'bash_scripts/', logfile)

			#copy ansible.cfg
			configSrc = constants.ROOT_PATH + '/data/' + 'config_templates/ansible.cfg'
			shutil.copy2(configSrc, directoryPath + 'ansible.cfg')

			#copy packer.json
			configSrc = constants.ROOT_PATH + '/data/' + 'config_templates/packer.json'
			with open(configSrc) as json_file:
				json_data = json.load(json_file)

			if bashScriptQuery.__len__() != 0:
				shellScriptJSONEntry = []
				for sqlRow in bashScriptQuery:
					shellScriptJSONEntry.append('bash_scripts/' + str(sqlRow).split('/')[-1])
				#add provisioner to packer json for the scripts
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

			#add forced playbooks first to main yaml
			for sqlRow in forcedAnsiblePlaybooksQuery:
				mainYaml.write("      - include: ansible_playbooks/" + str(sqlRow[1]).split('/')[-1] + "\n")
				mainYaml.write("        ignore_errors: yes\n")

			#add user playbooks
			for sqlRow in ansiblePlaysQuery:
				mainYaml.write("      - include: ansible_playbooks/" + str(sqlRow[1]).split('/')[-1] + "\n")
				mainYaml.write("        ignore_errors: yes\n")

			mainYaml.write("\n")

			#add all roles
			if forcedAnsibleRolesQuery.__len__() != 0 or ansibleRolesQuery.__len__() != 0:
				mainYaml.write("    roles:\n")
				for sqlRow in forcedAnsibleRolesQuery:
					mainYaml.write("      - " + str(sqlRow[1]).split('/')[-1] + "\n")
				for sqlRow in ansibleRolesQuery:
					mainYaml.write("      - " + str(sqlRow[1]).split('/')[-1] + "\n")
			mainYaml.close()


			logfile.write("\nStarting packer process...\nPacker Output:\n")

			#run packer? check exit code?
			os.chdir(directoryPath)
			packerOutput = subprocess.check_output(constants.PACKER_PATH + ' build packer.json', shell=True).strip().decode('utf-8')
			logfile.write(packerOutput + "\n")




			#for debugging
			logfile.close()
			print("finished first run of thread")
			break



			sleep(3)