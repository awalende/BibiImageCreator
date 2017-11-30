from flasgger import swag_from
import re
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, send_file, current_app
from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.utils import constants
from src.utils import local_resource, checkings, constants
from pymysql import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
import subprocess



app_rest = Blueprint('moduleManagement', __name__)



def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False

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


#tested
@app_rest.route('/_getForcedModules', methods = ['GET'])
@swag_from('yamldoc/getForcedModules.yaml')
def getForcedModules():
	if not 'username' in session:
		return jsonify(error = 'not logged in.'), 401

	forcedModulesList = Modules.query.filter_by(isForced = 'true').all()
	return jsonify([i.serialize for i in forcedModulesList])


#tested
@app_rest.route('/_getModuleByID/<int:targetID>', methods = ['GET'])
@swag_from('yamldoc/getModuleByID.yaml')
def getModuleByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in.'), 401
	targetModule = Modules.query.filter_by(id = int(targetID)).first()
	if targetModule is None:
		return jsonify(error = 'there is no module with such id.'), 404
	if targetModule.owner != session['username'] and not isAdmin() and targetModule.isPrivate != 'false' and targetModule.isForced != 'true':
		return jsonify(error = 'not privileged'), 401
	return jsonify(targetModule.serialize)

#tested
@app_rest.route('/_uploadModule', methods=['POST'])
@swag_from('yamldoc/uploadModule.yaml')
def uploadModule():
	if not 'username' in session:
		return jsonify(error = 'not logged in.'), 401
	MODULE_TYPE = 1
	MODULE_TYPE_DIRECTORY = 2
	if request.method == 'POST':
		print(request.form)
		print(request.files['file'])
		if not request.files['file']:
			return jsonify(error = "ERROR: No File has been sent to me."), 400
		file = request.files['file']
		tupleExtension = checkings.categorizeAndCheckModule(file)
		if tupleExtension[0] == 'N/A':
			return jsonify(error = "ERROR: Could not categorize file. Make sure it is supported and has the right extension"), 400

		#check priviliges for forced modules, booleans from frontend are forced to strings
		isForced = 'false'
		if session['username'] == 'admin' and 'isForced' in request.form:
			if request.form['isForced'] == 'true' or request.form['isForced'] == 'false':
				isForced = request.form['isForced']


		formDataCheck = checkings.checkNewModuleForm(request.form)
		if not formDataCheck == 'okay':
			return jsonify(error = formDataCheck), 400



		timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')
		dbFileName = session['username'] +timestamp + file.filename

		#create new module object
		newModule = Modules(request.form['moduleName'],
							session['username'],
							request.form['moduleDescriptionText'],
							request.form['moduleVersion'],
							request.form['isPrivate'],
							tupleExtension[MODULE_TYPE],
							tupleExtension[MODULE_TYPE_DIRECTORY] + '/' + dbFileName,
							isForced)

		db_alch.session.add(newModule)
		db_alch.session.commit()

		file.save(os.path.join(constants.ROOT_PATH + '/' + tupleExtension[MODULE_TYPE_DIRECTORY],
							   secure_filename(dbFileName)))

	return jsonify(result = 'confirmed')


#tested
@app_rest.route('/_deleteModuleByID/<int:targetID>', methods = ['DELETE'])
@swag_from('yamldoc/deleteModuleByID.yaml')
def deleteModuleByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in.'), 401

	if request.method == 'DELETE':

		#try to find a module with this id an obtain an object
		toBeDeletedModule = Modules.query.filter_by(id = targetID).first()
		if toBeDeletedModule is None:
			return jsonify(error = 'There is no module with the id: ' + str(targetID)), 404

		#a module can be deleted if done by admin or by the owner of the module
		if session['username'] == 'admin' or toBeDeletedModule.owner == session['username']:
			Modules.query.filter_by(id = toBeDeletedModule.id).delete()
			db_alch.session.commit()
			return jsonify(result = 'confirmed')
		else:
			return jsonify(error = 'not privileged to delete module.'), 403

#tested
@app_rest.route('/_getFileByID/<int:targetID>', methods = ['GET'])
@swag_from('yamldoc/getFileByID.yaml')
def getFileByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401

	#get the desired module row
	targetModule = Modules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found'), 404

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged'), 403

	filepath = constants.ROOT_PATH + '/' + targetModule.path
	return send_file(filepath, as_attachment=True, mimetype='text/plain')


#isokay
#does not need any kind of security, everyone could run ansible-galaxy.
@app_rest.route('/_getGalaxySearchResult', methods=['POST'])
@swag_from('yamldoc/getGalaxySearchResult.yaml')
def getGalaxySearchResult():
	if request.method == 'POST':
		data = request.get_json()
		#there must be at least one search criteria present
		if not 'tag' in data and not 'author' in data:
			return jsonify(error = 'Invalid Input.'), 400
		moduleList = []
		#build command
		command = 'ansible-galaxy --ignore-certs search'
		if 'tag' in data and str(data['tag']).__len__() > 0:
			command = command + ' --galaxy-tags {}'.format(data['tag'])
		if 'author' in data and str(data['author']).__len__() > 0:
			command = command + ' --author {}'.format(data['author'])
		try:
			f = subprocess.check_output(command, shell=True).strip().decode("utf-8")
			#we need only the result after the 4th line
			result = f.splitlines()[4:]
		except Exception as e:
			return jsonify(error = 'Could not run ansible-galaxy or it crashed.'), 500
		for line in result:
			moduleName = re.findall("([^\s]+)", line)[0]
			newline = line.replace(str(moduleName), "").lstrip()
			tmpdict = {'module': moduleName, 'description': newline}
			moduleList.append(tmpdict)

		return jsonify(moduleList)

