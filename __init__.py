import os

from flask import Flask
import configparser
import sys

from src.routing.rest import app_rest
from src.routing.views import app
from src.sqlalchemy.db_alchemy import db
from src.sqlalchemy.db_model import Users
from src.utils import constants
from src.threads.workerThread import JobWorker



if __name__ == "__main__":
	flask_app = Flask(__name__)
	flask_app.register_blueprint(app)
	flask_app.register_blueprint(app_rest)

	constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))




	config = configparser.ConfigParser()
	configFileList = config.read(constants.ROOT_PATH + '/config/config.ini')
	if not configFileList:
		print('Could not find config file! Aborting')
		sys.exit(-1)
	#todo check if config entrys are existing and valid?
	constants.CONFIG = config




	#todo establish db connection and set admin account with password from config file, also check db
	databaseUser = constants.CONFIG['database']['db_user']
	databasePassword = constants.CONFIG['database']['db_password']
	databaseUrl = constants.CONFIG['database']['db_url']
	databaseDescriptor = "mysql+pymysql://{}:{}@{}".format(databaseUser, databasePassword, databaseUrl)
	flask_app.config['SQLALCHEMY_DATABASE_URI'] = databaseDescriptor

	db.init_app(flask_app)

	#try to create the database structure
	with flask_app.app_context():
		try:
			db.create_all()

			#check if admin exists and give it the password given in the config file
			adminAccount = Users.query.filter_by(name = 'admin').first()
			if adminAccount is None:
				print('No admin Account was found, creating one with credentials from the config file.')
				newAdminAccount = Users('admin', constants.CONFIG['admin']['admin_password'], 999, constants.CONFIG['admin']['admin_password'])
				db.session.add(newAdminAccount)
				db.session.commit()

		except Exception as e:
			print('Errors occured in the database part: {}'.format(str(e)))
			sys.exit(-1)





	#todo start worker thread, garbage collector thread

	#todo establish a logger?












	constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
	flask_app.debug = True
	flask_app.secret_key = os.urandom(5000)

	thread = JobWorker(flask_app)
	thread.setDaemon(True)
	thread.start()

	#create sql database structure from object representation




	flask_app.run()


