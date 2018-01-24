'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
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
	user = Users.query.filter_by(name = request.json['name']).first()
	if user is None:
		return jsonify('No user with such name'), 401
	enteredPassword = request.json['password']
	if check_password_hash(user.password, enteredPassword):
		session['username'] = user.name
		session['logged_in'] = True
		session['current'] = "Overview"
		return jsonify(status = 'authenticated.')
	else:
		return jsonify(error = 'Invalid username/password'), 401