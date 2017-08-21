from time import sleep
from src.utils import db_connector
import threading
import os
from src.utils import constants
import shutil
import datetime

'''
Main worker thread for executing pending build jobs.
'''
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
			logfile.write("********\n\nGathering Roles, Playbooks, Scripts to this tmp directory...\n")

			#todo update job entry progress to gather


			#build directory structure
			ansible_roles_path = directoryPath + "ansible_roles/"
			os.makedirs(ansible_roles_path)

			ansible_playbooks_path = directoryPath + "ansible_playbooks/"
			os.makedirs(ansible_playbooks_path)

			bash_script_path = directoryPath + "bash_scripts/"
			os.makedirs(bash_script_path)







			#for debugging
			logfile.close()
			print("finished first run of thread")
			break








			sleep(3)