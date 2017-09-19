import os

from flask import Flask

from src.routing.rest import app_rest
from src.routing.views import app
from src.sqlalchemy.db_alchemy import db
from src.utils import constants
from src.threads.workerThread import JobWorker

flask_app = Flask(__name__)
flask_app.register_blueprint(app)
flask_app.register_blueprint(app_rest)


flask_app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:master@localhost/bibicreator"
db.init_app(flask_app)

if __name__ == "__main__":
	constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
	flask_app.debug = True
	flask_app.secret_key = os.urandom(5000)

	thread = JobWorker(flask_app)
	thread.setDaemon(True)
	thread.start()

	#create sql database structure from object representation
	with flask_app.app_context():
		db.create_all()

	flask_app.run()


