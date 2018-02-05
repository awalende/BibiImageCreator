"""Module responsibel for backuping all data content of bibicreator."""
import time

import tarfile
import subprocess
from src.utils import constants
import os




def backupEverything():
	"""Backups the bibicreator contents and the database into a .tar archive in bck/"""
	print('Starting backup process.')
	#create a new tarfile
	with tarfile.open(constants.ROOT_PATH + '/bck/' + str(time.time()) + 'backup.tar.gz', 'w:gz') as tar:
		conf = constants.CONFIG

		#where to create the .tar archive?
		sqlFilePath =  constants.ROOT_PATH + '/bck/' + 'dbbackup.sql'

		#use mysqldump to dump the entire mysql database into an .sql file
		subprocess.Popen('mysqldump -h {} -u {} --password={} {} > {}'.format(conf.db_url.split('/')[0],
																			  conf.db_user,
																			  conf.db_password,
																			  conf.db_url.split('/')[-1],
																			  sqlFilePath),
						 shell=True)
		#add all data and remove tmp files.
		tar.add(constants.ROOT_PATH + '/data/', arcname=os.path.basename(constants.ROOT_PATH + '/data/bck/'))
		tar.add(sqlFilePath, arcname = 'dump.sql')
		os.remove(sqlFilePath)
	print('Backup complete.')
