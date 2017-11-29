import os

from flask import Flask

from werkzeug.security import check_password_hash, generate_password_hash


import configparser
import sys
import logging
from flasgger import Swagger


from src.routing.rest import app_rest
from src.routing.views import app

from src.routing.API.userManagement import app_rest as userManagement_api
from src.routing.API.moduleManagement import app_rest as moduleManagement_api
from src.routing.API.jobManagement import app_rest as jobManagement_api
from src.routing.API.playlists import app_rest as playlists_api
from src.routing.API.history import app_rest as history_api

from src.sqlalchemy.db_alchemy import db
from src.sqlalchemy.db_model import Users
from src.threads.threadManager import ThreadManager
from src.utils import constants, checkings
from src.threads.workerThread import JobWorker
from src.threads.cleanUpThread import JobCleaner
from src.utils.backup import backupEverything
from src.openstack_api.openstackApi import OpenStackConnector

from src.configuration.config import Configuration




flask_app = Flask(__name__)

#register rest api blueprints
flask_app.register_blueprint(app)
flask_app.register_blueprint(app_rest)
flask_app.register_blueprint(userManagement_api)
flask_app.register_blueprint(moduleManagement_api)
flask_app.register_blueprint(jobManagement_api)
flask_app.register_blueprint(playlists_api)
flask_app.register_blueprint(history_api)

Swagger(flask_app)

constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

configINI = configparser.ConfigParser()
configFileList = configINI.read(constants.ROOT_PATH + '/config/config.ini')
if not configFileList:
	print('Could not find config file! Aborting')
	sys.exit(-1)

config = Configuration(configINI)
constants.CONFIG = config

databaseDescriptor = "mysql+pymysql://{}:{}@{}".format(config.db_user, config.db_password, config.db_url)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = databaseDescriptor


#check if necessary tools are available for proper BibiCreator Usage
if not checkings.checkToolAvailability():
	print('CRITICAL: Not all neccesarry tools are available for BibiCreator to work properly....exiting.')
	sys.exit(-1)

db.init_app(flask_app)


# try to create the database structure, exit out when there is no db connection
with flask_app.app_context():
	try:
		db.create_all()
		# check if admin exists and give it the password given in the config file
		adminAccount = Users.query.filter_by(name='admin').first()
		if adminAccount is None:
			print('No admin Account was found, creating one with credentials from the config file.')
			newAdminAccount = Users('admin', generate_password_hash(config.admin_password), 999, config.admin_email)
			db.session.add(newAdminAccount)
			db.session.commit()
	except Exception as e:
		print('Errors occured in the database part: {}'.format(str(e)))
		sys.exit(-1)

# set a global openstack connection
constants.OS_CONNECTION = OpenStackConnector(config.os_user, config.os_password, config.os_project_name,
											 config.os_auth_url, config.os_user_domain_id,
											 config.os_project_domain_name)


#backup
if config.auto_backup:
	print('Auto backup is enabled by config.')
	backupEverything()




constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
flask_app.debug = True
flask_app.secret_key = os.urandom(5000)

thread = ThreadManager(flask_app)
thread.setDaemon(True)
thread.start()

if __name__ == "__main__":
	flask_app.run(debug=True, use_reloader = False, host='0.0.0.0')


