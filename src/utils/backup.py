
import time

import tarfile
import subprocess
from src.utils import constants
import os




def backupEverything():


	print('Starting backup process.')
	with tarfile.open(constants.ROOT_PATH + '/bck/' + str(time.time()) + 'backup.tar.gz', 'w:gz') as tar:
		conf = constants.CONFIG

		sqlFilePath =  constants.ROOT_PATH + '/bck/' + 'dbbackup.sql'

		subprocess.Popen('mysqldump -h {} -u {} --password={} {} > {}'.format(conf.db_url.split('/')[0],
																			  conf.db_user,
																			  conf.db_password,
																			  conf.db_url.split('/')[-1],
																			  sqlFilePath),
						 shell=True)
		tar.add(constants.ROOT_PATH + '/data/', arcname=os.path.basename(constants.ROOT_PATH + '/data/bck/'))
		tar.add(sqlFilePath, arcname = 'dump.sql')
		os.remove(sqlFilePath)
	print('Backup complete.')
