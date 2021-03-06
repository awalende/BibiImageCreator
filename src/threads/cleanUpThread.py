"""This module is responsible for keeping the integrity between local data and database."""

import threading
import shutil
import time
from src.utils import constants
import os
from src.sqlalchemy.db_model import *
from src.sqlalchemy.db_alchemy import db as db_alch




def dirIntegrity(module_path, modlist):
	"""Checks if module files from database are existing on the local machine.

	Args:
		module_path: The installation script path of the module.
		modlist: A list of modules.

	"""
	dirlist = os.listdir(module_path)
	for filename in dirlist:
		if filename not in modlist:
			print("WARNING: {} does not to appear in db, removing.".format(module_path + filename))
			os.remove(module_path + filename)


class JobCleaner(threading.Thread):
	"""Class with the job to clean up false links in the module database."""


	def __init__(self, app):
		"""Initiliazes a JobCleaner object.

		Args:
			app: The flask app context.

		"""
		self.DEADLINE_MINUTES = 60
		self.app = app
		threading.Thread.__init__(self)


	def run(self):
		"""Runs the thread in an eternal loop, checking constantly the integrity of the database."""
		with self.app.app_context():

			#before the server starts, mark all jobs as ABORTED, when they were building right before the server went down the last time
			for job in Jobs.query.filter_by(status = 'in_progress').all():
				job.status = 'ABORTED'
			db_alch.session.commit()

			# delete all temporary unused galaxy modules
			subquery = (Modules.query.join(jobsXmodules).all())
			subquery = subquery + (Modules.query.join(playlistXmodules).all())
			ids = [item.id for item in subquery]
			ids = list(set(ids))
			query = Modules.query.filter(Modules.id.notin_(ids)).filter_by(module_type='GALAXY').all()

			#delete galaxy modules from db
			for module in query:
				db_alch.session.delete(module)
				db_alch.session.commit()

			db_alch.session.commit()

			# delete all non-referenced history modules
			subquery = (HistoryModules.query.join(historyXhistoryModules).all())
			ids = [item.id for item in subquery]
			query = HistoryModules.query.filter(HistoryModules.id.notin_(ids)).all()
			for module in query:
				db_alch.session.delete(module)
				db_alch.session.commit()

			# delete all invalid local files, who do not match with the db
			db_alch.session.commit()
			moduleList = Modules.query.all()
			modlist = [module.path.split('/')[-1] for module in moduleList]

			#do all db entrys still have their files on the local machine?
			dirIntegrity(constants.ROOT_PATH + constants.MODULES_DIRECTORY + 'ansible_roles/', modlist)
			dirIntegrity(constants.ROOT_PATH + constants.MODULES_DIRECTORY + 'ansible_playbooks/', modlist)
			dirIntegrity(constants.ROOT_PATH + constants.MODULES_DIRECTORY + 'bash_scripts/', modlist)

			#Delete finished jobs after a while.
			while True:
				time.sleep(10)
				for job in Jobs.query.filter_by(status = 'BUILD OKAY').all():
					currentUNIX_minutes = int(time.time() / 60)
					jobUNIX_minutes = int(time.mktime(job.date.timetuple()) / 60)

					if (currentUNIX_minutes - jobUNIX_minutes) > self.DEADLINE_MINUTES:
						directoryPath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/'
						shutil.rmtree(directoryPath, ignore_errors=True)
						db_alch.session.delete(job)
						db_alch.session.commit()














