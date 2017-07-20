from flask import Flask
from src.utils import constants
import logging
from src.routing.views import app
from src.routing.rest import app_rest
import os


flask_app = Flask(__name__)
flask_app.register_blueprint(app)
flask_app.register_blueprint(app_rest)


if __name__ == "__main__":
	constants.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
	flask_app.debug = True
	flask_app.secret_key = os.urandom(5000)
	flask_app.run()
