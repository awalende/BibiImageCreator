from time import sleep
import threading
from src.threads.cleanUpThread import JobCleaner
from src.threads.workerThread import JobWorker
from src.utils import constants
import shutil
import datetime
import subprocess
import os
import json
import signal
import tarfile
from src.utils import packerUtils




from src.sqlalchemy.db_model import *
from src.sqlalchemy.db_alchemy import db as db_alch




class ThreadManager(threading.Thread):


	def __init__(self, app):

		self.lock = threading.Lock()
		self.app = app
		threading.Thread.__init__(self)
		print('Started ThreadManager')


	def run(self):
		thread = JobWorker(self.app, self.lock)
		thread.setDaemon(True)
		thread.start()



		thread1 = JobCleaner(self.app)
		thread1.setDaemon(True)
		thread1.start()

		while True:
			sleep(30)
			if thread.p is not None:
				thread.shutDownPacker()






