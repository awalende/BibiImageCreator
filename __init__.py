import os

from flask import Flask
import configparser

from src.routing.rest import app_rest
from src.routing.views import app
from src.sqlalchemy.db_alchemy import db
from src.utils import constants
from src.threads.workerThread import JobWorker



if __name__ == "__main__":
	flask_app = Flask(__name__)
	flask_app.register_blueprint(app)
	flask_app.register_blueprint(app_rest)

	flask_app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:master@localhost/bibicreator"
	db.init_app(flask_app)



	constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
	flask_app.debug = True
	flask_app.secret_key = os.urandom(5000)

	thread = JobWorker(flask_app)
	thread.setDaemon(True)
	thread.start()

	#create sql database structure from object representation
	with flask_app.app_context():
		db.create_all()

	#todo parse a config file, set constants


	#todo establish db connection and set admin account with password from config file, also check db


	#todo start worker thread, garbage collector thread

	#todo establish a logger?

	flask_app.run()


