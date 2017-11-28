from flasgger import swag_from
from flask import Blueprint, request, jsonify, send_file, current_app
from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.utils import constants
from src.utils import local_resource, checkings, constants
from pymysql import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash



app_rest = Blueprint('moduleManagement', __name__)


#tested
@app_rest.route('/_getOwnModules', methods = ['GET'])
@swag_from('yamldoc/getOwnModules.yaml')
def getOwnModules():
	if 'username' not in session:
		return jsonify(error = "not logged in."), 401
	try:
		moduleList = Modules.query.filter_by(owner = session['username'], isForced = 'false').filter(Modules.module_type != 'GALAXY').all()
		return jsonify([i.serialize for i in moduleList])
	except Exception as e:
		return jsonify('N/A'), 400


#tested
@app_rest.route('/_getPublicModules', methods = ['GET'])
@swag_from('yamldoc/getPublicModules.yaml')
def getPublicModules():
	if 'username' not in session:
		return jsonify(error = "not logged in.")

	#If the current user is the admin, give him EVERY Module from EVERY User
	if session['username'] == 'admin':
		moduleList = Modules.query.filter(Modules.owner != 'admin', Modules.module_type != 'GALAXY').all()
	#If current user is not the admin, send only modules which are set to public
	else:
		moduleList = Modules.query.filter((Modules.owner != session['username']), (Modules.isPrivate == 'false'), (Modules.module_type != 'GALAXY'), (Modules.isForced == 'false')).all()
	return jsonify([i.serialize for i in moduleList])