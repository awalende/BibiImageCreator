from flasgger import swag_from
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



app_rest = Blueprint('jobManagement', __name__)


def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


#tested
@app_rest.route('/_getJobs', methods = ['GET'])
@swag_from('yamldoc/getJobs.yaml')
def getJobs():
	if not 'username' in session:
		return jsonify(error = 'not privileged'), 401

	if session['username'] == 'admin':
		jobList = Jobs.query.all()
	else:
		jobList = Jobs.query.filter_by(owner = session['username']).all()

	return jsonify(list(reversed([i.serialize for i in jobList])))


#already ok
@app_rest.route('/_requestNewBuildFromPlaylist', methods=['POST'])
@swag_from('yamldoc/requestNewBuildFromPlaylist.yaml')
def requestNewBuildFromPlaylist():
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	if request.method == 'POST':

		try:
			debugMsg = ''
			data = request.get_json()
			user = session['username']
			#has the user reached max limit of allowed builds in the cloud?
			dbUser = Users.query.filter_by(name = user).first()
			#get all images in openstack from this particular user
			allUserImages = constants.OS_CONNECTION.getBibiCreatorImagesByUser(dbUser.name)
		except KeyError:
			return jsonify(error= "Inavlid Input"), 400


		if allUserImages.__len__() >= int(dbUser.max_images):
			return jsonify(error = 'You have reached your maximum limit of OpenStack Images.'), 409

		if not checkings.checkToolAvailability():
			return jsonify(error = 'Some of the necessary automation tools are not available. Please contact the administrator.'), 500

		playlistID = int(data['playlistID'])
		desiredJobName = data['jobName']
		#check if playlist exists
		playlist = Playlists.query.filter_by(id = playlistID).first()
		if playlist is None:
			return jsonify(error = 'No playlist with such id was found.'), 404
		#check if playlist is yours or admin
		if playlist.owner != session['username'] and not isAdmin():
			return jsonify(error = 'Not privileged to use this playlist.'), 403

		#build a copy of the list for privilege checking
		moduleList = list(playlist.modules)
		for moduleID in moduleList:
			#first check if the module even exists
			fetchedModule = Modules.query.filter_by(id = int(moduleID.id)).first()
			if fetchedModule is None:
				moduleList.remove(moduleID)
				debugMsg = debugMsg + "\n WARNING: There is no module with the id " + moduleID + " in the Database!"
				continue
			#is the current user allowed to use the module?
			if fetchedModule.owner != user and user != 'admin' and fetchedModule.isPrivate == 'true':
				moduleList.remove(moduleID)
				debugMsg = debugMsg + "\n This user is not allowed to use module id " + moduleID
				continue

		# build job in database
		newJob = Jobs(desiredJobName, session['username'], 'NEW', None,
					  constants.CONFIG.os_base_img_id, None)
		db_alch.session.add(newJob)
		db_alch.session.commit()

		# obtain the freshly created job object
		newJob = Jobs.query.filter_by(name=desiredJobName).first()

		# now fill the modules to the job
		for moduleID in moduleList:
			targetModule = Modules.query.filter_by(id=int(moduleID.id)).first()
			newJob.modules.append(targetModule)

		db_alch.session.commit()
		sleep(3)
		debugMsg = debugMsg + "\n Your Job has been created!"
		return jsonify(result = 'Confirmed, job has been created.')




#tested
@app_rest.route('/_requestNewBuild', methods=['POST'])
@swag_from('yamldoc/requestNewBuild.yaml')
def requestNewBuild():
	#todo I maybe have to put the debug messages into a list, instead of an concated string
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	if request.method == 'POST':
		try:
			debugMsg = ''
			data = request.get_json()
			moduleList = data['modules']
			desiredJobName = data['name']
			#remove duplicates
			moduleList = list(set(moduleList))
			#verify that this is a valid moduleList
			user = session['username']
		except KeyError:
			return jsonify(error = 'Invalid Input')

		# has the user reached max limit of allowed builds in the cloud?
		dbUser = Users.query.filter_by(name=user).first()
		# get all images in openstack from this particular user
		allUserImages = constants.OS_CONNECTION.getBibiCreatorImagesByUser(dbUser.name)

		if allUserImages.__len__() >= int(dbUser.max_images):
			return jsonify(error='You have reached your maximum limit of OpenStack Images.'), 409


		if not checkings.checkToolAvailability():
			return jsonify(error = 'Some of the necessary automation tools are not available. Please contact the administrator.'), 500

		#check first if the jobname already exists
		possibleExistingJob = Jobs.query.filter_by(name = desiredJobName).first()
		if possibleExistingJob is not None:
			debugMsg = debugMsg + "\n ERROR: Job Name already exists."
			return jsonify(result=['error', debugMsg])

		#check if module entrys are valid by checking permissions and ownership of each module
		for moduleID in moduleList:
			#first check if the module even exists
			fetchedModule = Modules.query.filter_by(id = int(moduleID)).first()
			if fetchedModule is None:
				moduleList.remove(moduleID)
				debugMsg = debugMsg + "\n WARNING: There is no module with the id " + moduleID + " in the Database!"
				continue
			#is the current user allowed to use the module?
			if fetchedModule.owner != user and user != 'admin' and fetchedModule.isPrivate == 'true':
				moduleList.remove(moduleID)
				debugMsg = debugMsg + "\n This user is not allowed to use module id " + moduleID
				continue

		#build job in database
		newJob = Jobs(desiredJobName, session['username'], 'NEW', None, constants.CONFIG.os_base_img_id, None)
		db_alch.session.add(newJob)
		db_alch.session.commit()

		#obtain the freshly created job object
		newJob = Jobs.query.filter_by(name = desiredJobName).first()

		#now fill the modules to the job
		for moduleID in moduleList:
			targetModule = Modules.query.filter_by(id = int(moduleID)).first()
			newJob.modules.append(targetModule)

		#register ansible galaxy modules (temporarely)
		if 'galaxy' in data:
			for galaxyModule in data['galaxy']:
				name = galaxyModule['module']
				descr = galaxyModule['description']
				mod = Modules(name, session['username'], descr, 'n/a', 'n/a', 'GALAXY', 'n/a', 'false')
				newJob.modules.append(mod)
		db_alch.session.commit()
		sleep(3)
		debugMsg = debugMsg + "\n Your Job has been created!"
		return jsonify(result=['confirmed', 'Your job has been created!'])

	return jsonify(error = 'N/A')


#tested
@app_rest.route('/_getCrashLog/<int:targetID>', methods = ['GET'])
@swag_from('yamldoc/getCrashLog.yaml')
def getCrashLog(targetID):
	#get the job

	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	job = Jobs.query.filter_by(id = int(targetID)).first()
	if job is None:
		return jsonify(error = 'No job with such id was found'), 404
	#check privileges
	if job.owner != session['username'] and not isAdmin():
		return jsonify(error = 'not privileged'), 403
	#send the log
	filepath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/log.txt'
	return send_file(filepath, as_attachment=True, mimetype='text/plain')


# tested
@app_rest.route('/_removeJobByID/<int:id>', methods=['DELETE'])
@swag_from('yamldoc/removeJobByID.yaml')
def removeJobByID(id):
	if not 'username' in session:
		return jsonify(error='not logged in'), 401
	if request.method == 'DELETE':

		# obtain the job from db
		job = Jobs.query.filter_by(id=id).first()
		if job is None:
			return jsonify(error='Could not find job with this id.'), 404

		# check privileges
		if job.owner != session['username'] and not isAdmin():
			return jsonify(error='Not privileged.'), 403

		# check if its not running right now
		if job.status != 'ABORTED' and job.status != 'BUILD OKAY':
			return jsonify(error='Build is still running, wait for it to halt.'), 500

		# otherwise kill it with fire
		directoryPath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/'
		shutil.rmtree(directoryPath, ignore_errors=True)
		db_alch.session.delete(job)
		db_alch.session.commit()

		return jsonify(result='confirmed')



