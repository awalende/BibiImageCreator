'''This module lists all REST calls for authentication.
Documentation for these functions are created by swagger in apidocs/
You should use the interactive swagger documentation, hence it provides more and better documentation.
For the swagger documentation, simply start BibiCreator and point your browser to <URL>/apidocs
'''


from flasgger import swag_from
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, request, jsonify, send_file, current_app
from src.routing.views import session
from src.sqlalchemy.db_model import *


app_rest = Blueprint('authentication', __name__)


#tested
@app_rest.route('/_generateAuthCookie', methods=['POST'])
@swag_from('yamldoc/getAuthCookie.yaml')
def getAuthCookie():
	"""API Endpoint: Authenticates a user with name and password.
	You need to save the cookie response (in curl with "curl -c cookie.txt") and pass it everytime
	when you want to use an API Call from BibiCreator (in curl with "curl -b cookie.txt").
	This server uses flask secure session-cookies for authentication.
	By not providing the authentication cookie in further api calls, the server will treat you as an unauthorized person.


	Returns:
		A HTTP-Header response containing a flask-secure-session cookie.

	"""
	user = Users.query.filter_by(name = request.json['name']).first()
	if user is None:
		return jsonify('No user with such name'), 401
	enteredPassword = request.json['password']
	#if the user has been authenticated, create a new session.
	if check_password_hash(user.password, enteredPassword):
		session['username'] = user.name
		session['logged_in'] = True
		session['current'] = "Overview"
		return jsonify(status = 'authenticated.')
	else:
		return jsonify(error = 'Invalid username/password'), 401