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
from src.openstack_api import openstackApi
from src.openstack_api.openstackApi import OpenStackConnector

import src.configuration as conf
from src.configuration.config import Configuration


flask_app = Flask(__name__)
flask_app.register_blueprint(app)
flask_app.register_blueprint(app_rest)

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

db.init_app(flask_app)

# try to create the database structure, exit out when there is no db connection
with flask_app.app_context():
	try:
		db.create_all()
		# check if admin exists and give it the password given in the config file
		adminAccount = Users.query.filter_by(name='admin').first()
		if adminAccount is None:
			print('No admin Account was found, creating one with credentials from the config file.')
			newAdminAccount = Users('admin', config.admin_password, 999, config.admin_email)
			db.session.add(newAdminAccount)
			db.session.commit()
	except Exception as e:
		print('Errors occured in the database part: {}'.format(str(e)))
		sys.exit(-1)

# set a global openstack connection
constants.OS_CONNECTION = OpenStackConnector(config.os_user, config.os_password, config.os_project_name,
											 config.os_auth_url, config.os_user_domain_id,
											 config.os_project_domain_name)

# todo start worker thread, garbage collector thread

# todo establish a logger?

constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
flask_app.debug = True
flask_app.secret_key = os.urandom(5000)

thread = JobWorker(flask_app)
thread.setDaemon(True)
thread.start()

if __name__ == "__main__":
	flask_app.run()


