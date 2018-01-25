'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
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


"""This module lists all REST calls for history.
Documentation for these functions are created by swagger in apidocs/
"""

app_rest = Blueprint('history', __name__)

def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


#tested
@app_rest.route('/_getHistory', methods = ['GET'])
@swag_from('yamldoc/getHistory.yaml')
def getHistory():
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


