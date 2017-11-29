
import re
import os
from time import sleep
from werkzeug.security import check_password_hash, generate_password_hash
import subprocess
import datetime
import time

from flask import Blueprint, request, jsonify, send_file, current_app
from pymysql import IntegrityError
from werkzeug.utils import secure_filename


from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.utils import local_resource, checkings, constants
import shutil
import tarfile


app_rest = Blueprint('app_rest', __name__)

DB_CREDENTIALS = ('localhost', 'root', 'master', 'bibicreator')



def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


#tested
@app_rest.route('/_getAuthCookie', methods=['GET', 'POST'])
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
		return jsonify(error = 'Invalid username/password')

#tested
@app_rest.route('/_getHealth')
def getHealth():
	try:
		if session['username'] == 'admin':
			randomDict = {'cpu_name' : local_resource.get_processor_name(),
						  'cpu_load' : local_resource.get_cpu_load(),
						  'ram_usage': local_resource.get_ram_percent()}
			return jsonify(randomDict)
		else:
			return jsonify(error='not privileged')
	except KeyError:
		return jsonify(error = 'not privileged')

#tested
@app_rest.route('/_getVersions')
def getVersions():
	dictV = {}
	dictV['ansible'] = local_resource.get_app_version('ansible --version | head -n 1')
	dictV['packer'] = local_resource.get_app_version(constants.CONFIG.packer_path + ' version')
	dictV['db'] = local_resource.get_app_version('mysql --version')
	return jsonify(dictV)







#only tested in backend
#used in history_overview.html
@app_rest.route('/_getOsIDFromOSName/<os_image_name>', methods=['GET'])
def getOSIDFromOSName(os_image_name):
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')

	if request.method == 'GET':
		if not os_image_name:
			return jsonify(error = 'Invalid Input')
		os_image_id = constants.OS_CONNECTION.findImageIdByName(os_image_name)
		return jsonify(result = os_image_id)
	return jsonify(error = 'not allowed')




#tested
@app_rest.route('/_getOSImages')
def getOSImages():
	if not 'username' in session:
		return jsonify(error = 'not logged in.')
	if isAdmin():
		images = constants.OS_CONNECTION.getAllBibiCreatorImages()
	else:
		images = constants.OS_CONNECTION.getBibiCreatorImagesByUser(session['username'])


	imageList = []
	for image in images:
		entry = {'name' : image.name, 'status': image.status, 'created_at': image.created_at, 'size': image.size, 'id': image.id}
		imageList.append(entry)

	return jsonify(imageList)


#tested
@app_rest.route('/_deleteOSImageByName/<imageName>', methods=['DELETE'])
def deleteOSImageByName(imageName):
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	if request.method == 'DELETE':
		if imageName is None:
			return jsonify(error = 'Invalid Input.')
		if isAdmin():
			images = constants.OS_CONNECTION.getAllBibiCreatorImages()
		else:
			images = constants.OS_CONNECTION.getBibiCreatorImagesByUser(session['username'])
		for image in images:
			if image.name == imageName:
				constants.OS_CONNECTION.deleteImageByName(image.name)
				return jsonify(result = 'confirmed')
		return jsonify(error = 'could not find image with such name.')

	return jsonify(error = 'Invalid Method.')







#tested
@app_rest.route('/_deleteHistoryByID/<int:targetID>', methods = ['DELETE'])
def deleteHistoryByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	#try to obtain this desired history from the db
	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'No History found with this id.')

	#check privileges
	if session['username'] != 'admin' and targetHistory.owner != session['username']:
		return jsonify(error = 'not privileged')

	db_alch.session.delete(targetHistory)
	db_alch.session.commit()
	shutil.rmtree(constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id), ignore_errors=True)
	return jsonify(result = 'confirmed')




#tested
@app_rest.route('/_updateHistoryComment', methods=['PUT'])
def updateHistoryComment():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	if request.method == 'PUT':
		data = request.get_json()
		#try to obtain this desired history from the db
		targetHistory = History.query.filter_by(id = int(data['targetID'])).first()
		if targetHistory is None:
			return jsonify(error = 'No History found with this id.')
		#check privileges
		if session['username'] != 'admin' and targetHistory.owner != session['username']:
			return jsonify(error = 'not privileged')
		targetHistory.commentary = data['commentary']
		db_alch.session.commit()
		return jsonify(result = 'confirmed')
	return jsonify(error = 'Unknown Error.')









#todo this is still request based
#todo need to test this in real environment
@app_rest.route('/_getHistoryLogByID/<int:targetID>', methods = ['GET'])
def getHistoryLogByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetHistory.owner != session['username'] and targetHistory.isPrivate == 'false':
		return jsonify(error = 'not privileged')


	filepath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id) + '/log.txt'
	#print('trying to send file {}'.format(filepath))
	return send_file(filepath, as_attachment=True, mimetype='text/plain')





#needs testing in real environment
@app_rest.route('/_getBackupHistoryByID/<int:targetID>', methods = ['GET'])
def getBackupHistoryByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetHistory.owner != session['username'] and targetHistory.isPrivate == 'false':
		return jsonify(error = 'not privileged')


	filepath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id) + '/backup.tar.gz'
	print('trying to send file {}'.format(filepath))
	return send_file(filepath, as_attachment=True, mimetype='application/gzip')

@app_rest.route('/_getHistoryModuleByID/<int:targetID>', methods = ['GET'])
def getHistoryModuleByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in')
	targetModule = HistoryModules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged')

	return jsonify(targetModule.serialize)

#needs testing
@app_rest.route('/_getHistoryModuleFileByID/<int:targetID>', methods = ['GET'])
def getHistoryModuleFileByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetModule = HistoryModules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged')

	filepath = constants.ROOT_PATH + '/' + targetModule.path


	if os.path.isdir(filepath):

		#todo filename creation is weird
		with tarfile.open(filepath+'bac.tar.gz', "w:gz") as tar:
			tar.add(filepath, arcname=os.path.basename(filepath))
			return send_file(filepath+'bac.tar.gz', as_attachment=True, mimetype='text/plain')
	return send_file(filepath, as_attachment=True, mimetype='text/plain')


#isokay
#does not need any kind of security, everyone could run ansible-galaxy.
@app_rest.route('/_getGalaxySearchResult', methods=['POST'])
def getGalaxySearchResult():
	if request.method == 'POST':
		data = request.get_json()
		#there must be at least one search criteria present
		if not 'tag' in data and not 'author' in data:
			return jsonify(error = 'Invalid Input.')
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
			return jsonify(error = 'Could not run ansible-galaxy or it crashed.')
		for line in result:
			moduleName = re.findall("([^\s]+)", line)[0]
			newline = line.replace(str(moduleName), "").lstrip()
			tmpdict = {'module': moduleName, 'description': newline}
			moduleList.append(tmpdict)

		return jsonify(moduleList)



#tested
@app_rest.route('/_changeBaseImgByID/<imgID>', methods=['PUT'])
def changeBaseImgByID(imgID):
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')

	if not isAdmin():
		return jsonify(error = 'Not privileged.')

	if request.method == 'PUT':
		constants.CONFIG.os_base_img_id = imgID
		return jsonify(result = 'confirmed')





###########ALCHEMY TESTS########################



def dirIntegrity(module_path, modlist):
	dirlist = os.listdir(module_path)
	for filename in dirlist:
		if filename not in modlist:
			print("WARNING: {} does not to appear in db, removing.".format(module_path + filename))
			os.remove(module_path + filename)


@app_rest.route('/_test')
def testroute():







	return jsonify()


