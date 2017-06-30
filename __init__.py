from flask import Flask
from src.routing.views import app
from src.routing.rest import app_rest
import os


flask_app = Flask(__name__)
flask_app.register_blueprint(app)
flask_app.register_blueprint(app_rest)


if __name__ == "__main__":
	flask_app.debug = True
	flask_app.secret_key = os.urandom(5000)
	flask_app.run()
