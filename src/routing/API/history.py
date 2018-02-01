'''This module lists all REST calls for history.
Documentation for these functions are created by swagger in apidocs/
You should use the interactive swagger documentation, hence it provides more and better documentation.
For the swagger documentation, simply start BibiCreator and point your browser to <URL>/apidocs
'''

from flasgger import swag_from
import os
from flask import Blueprint, request, jsonify, send_file, current_app
from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.utils import local_resource, checkings, constants
import shutil
import tarfile




app_rest = Blueprint('history', __name__)

def isAdmin():
	"""Checks if the currently logged in user is the administrator.

	Returns:
		True if admin.

	"""
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


#tested
@app_rest.route('/_getHistory', methods = ['GET'])
@swag_from('yamldoc/getHistory.yaml')
def getHistory():
	"""API Endpoint: Get list of all Historys for the currently logged in user. The administrator will retreive all Historys from every user.

	Returns:
		A JSON object containing a list of all user historys.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401
	#if admin, return every history made
	if session['username'] == 'admin':
		query = History.query.all()
		historyList = [i.serialize for i in query]
	else:
		query = History.query.filter_by(owner = session['username']).all()
		historyList = [i.serialize for i in query]
	return jsonify(historyList)


#tested
@app_rest.route('/_updateHistoryComment', methods=['PUT'])
@swag_from('yamldoc/updateHistoryComment.yaml')
def updateHistoryComment():
	"""API Endpoint: Update the comment for a history object targeted by id.
	Users can only change the commentary on their own historys,
	while administrators can modify every history in the system.


	Returns:
		A HTTP-Status code.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401
	if request.method == 'PUT':
		data = request.get_json()
		#try to obtain this desired history from the db
		targetHistory = History.query.filter_by(id = int(data['targetID'])).first()
		if targetHistory is None:
			return jsonify(error = 'No History found with this id.'), 404
		#check privileges
		if session['username'] != 'admin' and targetHistory.owner != session['username']:
			return jsonify(error = 'not privileged'), 403
		targetHistory.commentary = data['commentary']
		db_alch.session.commit()
		return jsonify(result = 'confirmed')
	return jsonify(error = 'Unknown Error.'), 400


#tested
@app_rest.route('/_deleteHistoryByID/<int:targetID>', methods = ['DELETE'])
@swag_from('yamldoc/deleteHistoryByID.yaml')
def deleteHistoryByID(targetID):
	"""API Endpoint: Deletes a History object by providing the id of the history object.
	Users can only delete their own History objects, while administrators can delete every history object.
	A deletion also deletes the local history module from disk and they can't be retreived anymore. Use with caution.

	Args:
		targetID(int): The to be deletet history by id.

	Returns:
		A HTTP-Status code.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401
	#try to obtain this desired history from the db
	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'No History found with this id.'), 404

	#check privileges
	if session['username'] != 'admin' and targetHistory.owner != session['username']:
		return jsonify(error = 'not privileged'), 403

	db_alch.session.delete(targetHistory)
	db_alch.session.commit()
	shutil.rmtree(constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id), ignore_errors=True)
	return jsonify(result = 'confirmed')


@app_rest.route('/_getHistoryLogByID/<int:targetID>', methods = ['GET'])
@swag_from('yamldoc/getHistoryLogByID.yaml')
def getHistoryLogByID(targetID):
	"""API Endpoint: Returns the build logfile stored in a history object for download.
	Logfiles show informations about the initial build process and contains log messages from packer and ansible.
	Users can only obtain logfiles from their own history, while the administrator can obtain logfiles from every history object in the system.

	Args:
		targetID(int): The id of the history, containing the desired logfile.

	Returns:
		A HTTP download prompt with the logfile attached.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401

	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'not found'), 404

	if session['username'] != 'admin' and targetHistory.owner != session['username'] and targetHistory.isPrivate == 'false':
		return jsonify(error = 'not privileged'), 403


	filepath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id) + '/log.txt'
	#print('trying to send file {}'.format(filepath))
	return send_file(filepath, as_attachment=True, mimetype='text/plain')


#needs testing
@app_rest.route('/_getHistoryModuleFileByID/<int:targetID>', methods = ['GET'])
@swag_from('yamldoc/getHistoryModuleFileByID.yaml')
def getHistoryModuleFileByID(targetID):
	"""API Endpoint: Returns the module file from a specific history module.
	Each created history object copies the used modules from the build as a history module object and registres this to the history.
	Users can only retreive their own history modules, while administrators can retreive every history module in the system.

	Args:
		targetID(int): The targeted history module by id, on were to obtain the installation script from.

	Returns:
		A HTTP download prompt.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401

	targetModule = HistoryModules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found'), 404

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged'), 403

	#build the standard file path for stored modules
	filepath = constants.ROOT_PATH + '/' + targetModule.path


	#if this installation script is a ansible role (a folder), use tar archiver.
	if os.path.isdir(filepath):
		#todo filename creation is weird
		#pack all contents into a tar
		with tarfile.open(filepath+'bac.tar.gz', "w:gz") as tar:
			tar.add(filepath, arcname=os.path.basename(filepath))
			return send_file(filepath+'bac.tar.gz', as_attachment=True, mimetype='text/plain')
	return send_file(filepath, as_attachment=True, mimetype='text/plain')

@app_rest.route('/_getHistoryModuleByID/<int:targetID>', methods = ['GET'])
@swag_from('yamldoc/getHistoryModuleByID.yaml')
def getHistoryModuleByID(targetID):
	"""API Endpoint: Returns the history module object specified by id.
	Users can only retreive their own history modules, while administrators can receive every history module.

	Args:
		targetID(int): The targeted history by id.

	Returns:
		A JSON object containing the desired history.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	targetModule = HistoryModules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found'), 404

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged'), 403

	return jsonify(targetModule.serialize)


#needs testing in real environment
@app_rest.route('/_getBackupHistoryByID/<int:targetID>', methods = ['GET'])
@swag_from('yamldoc/getBackupHistoryByID.yaml')
def getBackupHistoryByID(targetID):
	"""API Endpoint: Generates a backup archive of an already existing history record.
	Users are able to download an archive of their build from an registred history object.
	The archive contains all modules, logfiles and configuration files for packer and ansible.
	Users can only generate a backup archive of their own history objects, while administrators can
	do this on every history object in the system.

	Args:
		targetID(int): The targeted history by id on were to download an archive from.

	Returns:
		A HTTP download prompt.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401

	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'not found'), 404

	if session['username'] != 'admin' and targetHistory.owner != session['username'] and targetHistory.isPrivate == 'false':
		return jsonify(error = 'not privileged'), 403


	filepath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id) + '/backup.tar.gz'
	print('trying to send file {}'.format(filepath))
	return send_file(filepath, as_attachment=True, mimetype='application/gzip')


