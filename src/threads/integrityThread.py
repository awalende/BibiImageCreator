"""WARNING: deprecated. Needs to be deleted."""


import threading
import shutil
import time
import datetime
import logging
from src.utils import constants

from src.sqlalchemy.db_model import *
from src.sqlalchemy.db_alchemy import db as db_alch




class IntegrityCheck(threading.Thread):
	"""Not used anymore in the system. (deprecated)"""

	def __init__(self, app):
		threading.Thread.__init__(self)


	def run(self):
		with self.app.app_context():
			while True:
				time.sleep(10)

				#remove redundant galaxy modules from db

