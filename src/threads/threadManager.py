import time
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
		self.threadList = []
		self.lock = threading.Lock()
		self.app = app
		threading.Thread.__init__(self)
		print('Started ThreadManager')

	def checkForTTL(self, secondsToLive):
		currentTime = time.time()
		for thread in self.threadList:
			if thread.time is not None:
				if currentTime - thread.time > secondsToLive:
					thread.shutDownPacker()


	def run(self):
		for i in range(5):
			thread = JobWorker(self.app, self.lock)
			thread.setDaemon(True)
			thread.start()
			self.threadList.append(thread)



		thread1 = JobCleaner(self.app)
		thread1.setDaemon(True)
		thread1.start()

		while True:
			time.sleep(3)
			self.checkForTTL(60)












