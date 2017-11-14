import threading
import shutil
import time
import datetime
import logging
from src.utils import constants

from src.sqlalchemy.db_model import *
from src.sqlalchemy.db_alchemy import db as db_alch




class JobCleaner(threading.Thread):



	def __init__(self, app):
		self.DEADLINE_MINUTES = 5
		self.app = app
		threading.Thread.__init__(self)


	def run(self):
		with self.app.app_context():

			while True:

				time.sleep(3)

				for job in Jobs.query.filter_by(status = 'BUILD OKAY').all():
					currentUNIX_minutes = int(time.time() / 60)
					jobUNIX_minutes = int(time.mktime(job.date.timetuple()) / 60)

					if (currentUNIX_minutes - jobUNIX_minutes) > self.DEADLINE_MINUTES:
						directoryPath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/'
						shutil.rmtree(directoryPath, ignore_errors=True)
						db_alch.session.delete(job)
						db_alch.session.commit()
						#print('deleted job {}'.format('a'))








