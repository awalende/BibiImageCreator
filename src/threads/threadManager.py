'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
'''

import time
import threading
from src.threads.cleanUpThread import JobCleaner
from src.threads.workerThread import JobWorker




class ThreadManager(threading.Thread):
	"""The ThreadManager manages all worker and integrity threads from BibiCreator"""


	def __init__(self, app):
		"""Start up the threadmanager.

		Args:
			app: The flask app context.

		"""
		self.threadList = []

		#there exists one lock for all threads to borrow.
		self.lock = threading.Lock()

		self.app = app
		threading.Thread.__init__(self)
		print('Started ThreadManager')

	def checkForTTL(self, secondsToLive):
		"""Checks the uptime of a workerthread, which is currently building a new Image.
		Shut down the thread if the process takes too long.

		Args:
			secondsToLive: Threshold of time to live for this thread.

		"""
		currentTime = time.time()
		for thread in self.threadList:
			if thread.time is not None:
				if currentTime - thread.time > secondsToLive:
					thread.shutDownPacker()


	def run(self):
		"""Spins up all 5 worker threads."""
		for i in range(5):
			thread = JobWorker(self.app, self.lock)
			thread.setDaemon(True)
			thread.start()
			self.threadList.append(thread)



		thread1 = JobCleaner(self.app)
		thread1.setDaemon(True)
		thread1.start()

		while True:
			#constantly check the uptime of each worker thread, if needed kill the process.
			time.sleep(3)
			self.checkForTTL(60 * 60) #equals in one hour












