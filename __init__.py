'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
	-------------------------------------------------
	__init__.py
	This is the entrypoint of this application, which checks configurations
	and connects to all needed external applications. On finish, this starts
	up the Webservice BibiCreator.
'''

import os
from flask import Flask
from werkzeug.security import  generate_password_hash
import configparser
import sys
from flasgger import Swagger
from src.routing.views import app
from src.routing.API.userManagement import app_rest as userManagement_api
from src.routing.API.moduleManagement import app_rest as moduleManagement_api
from src.routing.API.jobManagement import app_rest as jobManagement_api
from src.routing.API.playlists import app_rest as playlists_api
from src.routing.API.history import app_rest as history_api
from src.routing.API.openStack import app_rest as openStack_api
from src.routing.API.administratorTools import app_rest as administratorTools_api
from src.routing.API.authentication import app_rest as authentication_api
from src.sqlalchemy.db_alchemy import db
from src.sqlalchemy.db_model import Users
from src.threads.threadManager import ThreadManager
from src.utils import constants, checkings
from src.utils.backup import backupEverything
from src.openstack_api.openstackApi import OpenStackConnector
from src.configuration.config import Configuration



#register a new flask application
flask_app = Flask(__name__)

#register rest api blueprints into this flask application
flask_app.register_blueprint(app)
flask_app.register_blueprint(userManagement_api)
flask_app.register_blueprint(moduleManagement_api)
flask_app.register_blueprint(jobManagement_api)
flask_app.register_blueprint(playlists_api)
flask_app.register_blueprint(history_api)
flask_app.register_blueprint(openStack_api)
flask_app.register_blueprint(administratorTools_api)
flask_app.register_blueprint(authentication_api)

#register a new documentation interface with Swagger
Swagger(flask_app)

#register the absolute root path of this application and make it globally available
constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

#start reading out the configuration file in /etc/bibicreator with a designated parser
configINI = configparser.ConfigParser()
configFileList = configINI.read('/etc/bibicreator/config.ini')
if not configFileList:
	print('Could not find config file! Aborting')
	sys.exit(-1)

#save the parsed configuration and make it globally available for all other modules
config = Configuration(configINI)
constants.CONFIG = config

#set up the mysql connection with credentials presented in the configuration file.
#also enable SQLAlchemy support for this flask application.
databaseDescriptor = "mysql+pymysql://{}:{}@{}".format(config.db_user, config.db_password, config.db_url)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = databaseDescriptor


#check if necessary tools are available for proper BibiCreator Usage. Exit out if they are not there.
if not checkings.checkToolAvailability():
	print('CRITICAL: Not all neccesarry tools are available for BibiCreator to work properly....exiting.')
	sys.exit(-1)

#fusion flask-sqlalchemy with the flask application
db.init_app(flask_app)


# try to create the database structure, exit out when there is no db connection
with flask_app.app_context():
	try:
		db.create_all()
		# check if admin exists and give it the password given in the config file
		adminAccount = Users.query.filter_by(name='admin').first()
		if adminAccount is None:
			print('No admin Account was found, creating one with credentials from the config file.')
			#creates a new admin account and pushes it to the database
			newAdminAccount = Users('admin', generate_password_hash(config.admin_password), 999, config.admin_email, 'dummy', 'local_admin')
			db.session.add(newAdminAccount)
			db.session.commit()
	except Exception as e:
		print('Errors occured in the database part: {}'.format(str(e)))
		sys.exit(-1)


# setup a global openstack connection
constants.OS_CONNECTION = OpenStackConnector(config.os_user, config.os_password, config.os_project_name,
											 config.os_auth_url, config.os_user_domain_id,
											 config.os_project_domain_name)

#check if the autobackup feature is enabled by the configuration file.
if config.auto_backup:
	print('Auto backup is enabled by config.')
	backupEverything()

#update absolute root path of this application
constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


#build data folder structure, if not existing already
if not os.path.exists(constants.ROOT_PATH + '/data/modules'):
	os.makedirs(constants.ROOT_PATH + '/data/modules')
	os.makedirs(constants.ROOT_PATH + '/data/modules/ansible_roles/')
	os.makedirs(constants.ROOT_PATH + '/data/modules/ansible_playbooks/')
	os.makedirs(constants.ROOT_PATH + '/data/modules/bash_scripts/')


#enable this for logging prints to apache2 error logfile, located in /var/log/apache2/
flask_app.debug = True
#generate a new secret key for new sessions.
flask_app.secret_key = os.urandom(5000)

#Startup all threads which controll the contents of the database.
thread = ThreadManager(flask_app)
thread.setDaemon(True)
thread.start()

#gets called when this application is NOT run via apache 2 webserver.
if __name__ == "__main__":
	flask_app.run(debug=True, use_reloader = False, host='0.0.0.0')


