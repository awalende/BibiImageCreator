
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


#tested
@app_rest.route('/_getUsers')
def getUsers():
	"""Returns all Users available from the database
	    This is using docstrings for specifications.
	    ---
	    tags:
	      - Usermanagement

	    security:
	      - cookieAuth: []
	    parameters:
	      - name: palette
	        in: path
	        type: string
	        enum: ['all', 'rgb', 'cmyk']
	        required: true
	        default: all
	    definitions:
	      Palette:
	        type: object
	        properties:
	          palette_name:
	            type: array
	            items:
	              $ref: '#/definitions/Color'
	      Color:
	        type: string
	    responses:
	      200:
	        description: A list of colors (may be filtered by palette)
	        schema:
	          $ref: '#/definitions/Palette'
	        examples:
	          rgb: ['red', 'green', 'blue']
	      301:
	        description: You suck at life.
	    """
	if 'username' in session and session['username'] == 'admin':
		sqlquery = Users.query.all()
		return jsonify([i.serialize for i in sqlquery])
	return jsonify(error = 'not privileged'), 401

#tested
#used in user_management.html
@app_rest.route('/_deleteUser/<int:userID>', methods = ['DELETE'])
def deleteUser(userID):
	if not isAdmin():
		return jsonify(error = 'Not authorized'), 401
	print("Got a user id I have to delete: " + str(userID))
	if userID == 1:
		print('Cant delete Admin Account....like cutting off an own leg :( ')
		return jsonify(0)
	try:
		targetUserID = Users.query.filter_by(id=userID).first()
		if targetUserID is None:
			return jsonify(error= 'no user with such id was found.')

		#actual delete process
		Users.query.filter_by(id=userID).delete()
		db_alch.session.commit()

		return jsonify(result = 'confirmed')
	except Exception as e:
		print(e)
	return jsonify(0)


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
@app_rest.route('/_getUserImageLimit')
def getUserImageLimit():
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	#query the user
	dbUser = Users.query.filter_by(name = session['username']).first()
	maxLimit = dbUser.max_images
	#get current usage from os

	try:
		if isAdmin():
			images = constants.OS_CONNECTION.getAllBibiCreatorImages()
		else:
			images = constants.OS_CONNECTION.getBibiCreatorImagesByUser(session['username'])

	except Exception as e:
		return jsonify(error = 'could not connect to openstack')

	currentUsage = len(images)
	return jsonify({'currentUsage': currentUsage, 'maxLimit' : maxLimit})


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
@app_rest.route('/_createUser', methods = ['POST'])
def createUser():
	if not isAdmin():
		return jsonify(error='not privileged')


	if request.method == 'POST':
		userDict = request.get_json()
		if checkings.checkPassedUserFormular(userDict):
			try:
				new_user = Users(userDict['userName'], generate_password_hash(userDict['userPassword']), userDict['userMax'], userDict['userEmail'])
				db_alch.session.add(new_user)
				db_alch.session.commit()
				return jsonify(result = 'confirmed')
			except IntegrityError as e:
				code, msg = e.args
				return jsonify(result = str(code))
			except KeyError:
				return jsonify(error = 'Invalid Input.')


#tested
@app_rest.route('/_changeUserPassword', methods=['PUT'])
def changeUserPassword():
	if 'username' not in session:
		return jsonify(error = 'Not logged in')

	if request.method == 'PUT':

		data = request.get_json()
		if not all(k in data for k in ('oldPassword', 'newPassword', 'repeatNewPassword')):
			return jsonify(error = 'Invalid Input.')

		#check if oldPassword matches
		user = Users.query.filter_by(name = session['username']).first()
		if not check_password_hash(user.password, data['oldPassword']):
			return jsonify(error = 'Old password does not match.')

		if str(data['newPassword']).__len__() <= 4:
			return jsonify(error = 'Password is too short, at least 5 character!')

		if data['newPassword'] != data['repeatNewPassword']:
			return jsonify(error = 'New password is not the same is the repeated password!')

		#set the new password in db
		user.password = generate_password_hash(data['newPassword'])
		db_alch.session.commit()
		session['logged_in'] = False
		session.pop(session['username'], None)
		return jsonify(result = 'Confirmed.')
	return jsonify(error = 'Not allowed.')




#tested
@app_rest.route('/_updateUser', methods=['PUT'])
def updateUser():
	if 'username' not in session:
		return jsonify(error = 'Not logged in.')
	if not isAdmin():
		return jsonify(error = 'Not privileged.')

	if request.method == 'PUT':
		#first get actual user data

		data = request.get_json()
		try:

			userRow = Users.query.filter_by(id = int(data['userID'])).first()
			if userRow is None:
				return jsonify(error = 'can\'t update user, does not exist.')


			if 'password' in data:
				if not data['password'] == '':
					userRow.password = generate_password_hash(data['password'])

			if 'email' in data:
				if not data['email'] == '':
					userRow.email = data['email']

			if 'max_instances' in data:
				if not data['max_instances'] == '':
					userRow.max_images = data['max_instances']

			db_alch.session.commit()
			return jsonify(result = 'confirmed')
		except IntegrityError as e:
			code, msg = e.args
			return jsonify(result = str(code))


#tested
@app_rest.route('/_getOwnModules', methods = ['GET'])
def getOwnModules():
	try:
		moduleList = Modules.query.filter_by(owner = session['username'], isForced = 'false').filter(Modules.module_type != 'GALAXY').all()
		return jsonify([i.serialize for i in moduleList])
	except Exception as e:
		return jsonify('N/A')

#tested
@app_rest.route('/_getPublicModules', methods = ['GET'])
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
def getForcedModules():
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	forcedModulesList = Modules.query.filter_by(isForced = 'true').all()
	return jsonify([i.serialize for i in forcedModulesList])

#tested
@app_rest.route('/_getModuleByID', methods = ['GET'])
def getModuleByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	#todo check if input is valid
	targetID = request.args.get('id', 0, type=str)

	targetModule = Modules.query.filter_by(id = int(targetID)).first()
	if targetModule is None:
		return jsonify(error = 'there is no module with such id.')

	return jsonify(targetModule.serialize)

#tested
@app_rest.route('/_getJobs', methods = ['GET'])
def getJobs():
	if not 'username' in session:
		return jsonify(error = 'not privileged')

	if session['username'] == 'admin':
		jobList = Jobs.query.all()
	else:
		jobList = Jobs.query.filter_by(owner = session['username']).all()

	return jsonify(list(reversed([i.serialize for i in jobList])))




#tested
@app_rest.route('/_deleteModuleByID/<int:targetID>', methods = ['DELETE'])
def deleteModuleByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	if request.method == 'DELETE':

		#try to find a module with this id an obtain an object
		toBeDeletedModule = Modules.query.filter_by(id = targetID).first()
		if toBeDeletedModule is None:
			return jsonify(error = 'There is no module with the id: ' + str(targetID))

		#a module can be deleted if done by admin or by the owner of the module
		if session['username'] == 'admin' or toBeDeletedModule.owner == session['username']:
			Modules.query.filter_by(id = toBeDeletedModule.id).delete()
			db_alch.session.commit()
			return jsonify(result = 'confirmed')
		else:
			return jsonify(error = 'not privileged to delete module.')

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
@app_rest.route('/_getFileByID/<int:targetID>', methods = ['GET'])
def getFileByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	#get the desired module row
	targetModule = Modules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged')

	filepath = constants.ROOT_PATH + '/' + targetModule.path
	return send_file(filepath, as_attachment=True, mimetype='text/plain')

#tested
@app_rest.route('/_registerNewPlaylist', methods=['POST'])
def registerNewPlaylist():
	if not 'username' in session:
		return jsonify(error = 'not logged in')


	if request.method == 'POST':
		data = request.get_json()
		try:
			moduleList = list(set(data['modules']))
			playlistName = data['playlistName']
			user = session['username']
		except KeyError as e:
			return jsonify(error = 'Invalid input')


		#check if there is already a playlist with this name
		possibleExistingPlaylist = Playlists.query.filter(Playlists.owner == user, Playlists.name == playlistName).first()
		if possibleExistingPlaylist is not None:
			return jsonify(error = 'Playlistname already exists.')

		#check permissions of modules
		for moduleID in moduleList:
			#check if the module even exists
			fetchedModule = Modules.query.filter_by(id = int(moduleID)).first()
			if fetchedModule is None:
				moduleList.remove(moduleID)
				continue
			#is the current user allowed to use this module?
			if fetchedModule.owner != user and user != 'admin' and fetchedModule.isPrivate == 'false':
				moduleList.remove(moduleID)
				continue

		#build playlist db entry
		if 'description' in data:
			description = data['description']
		else:
			description = 'n/a'

		newPlaylist = Playlists(playlistName, user, description)
		db_alch.session.add(newPlaylist)
		db_alch.session.commit()

		#refetch new playlist from db
		newPlaylist = Playlists.query.filter(Playlists.owner == user, Playlists.name == playlistName).first()

		#add modules to playlist
		for moduleID in moduleList:
			targetModule = Modules.query.filter_by(id=int(moduleID)).first()
			newPlaylist.modules.append(targetModule)

		#register ansible galaxy modules (temporarely)
		if 'galaxy' in data:
			for galaxyModule in data['galaxy']:
				name = galaxyModule['module']
				descr = galaxyModule['description']
				mod = Modules(name, session['username'], descr, 'n/a', 'n/a', 'GALAXY', 'n/a', 'false')
				newPlaylist.modules.append(mod)

		db_alch.session.commit()

		sleep(3)
		return jsonify(result = 'Playlist has been saved!')


	return jsonify(error = 'Invalid request.')


#todo add warnings in a message
#tested
@app_rest.route('/_removeModulesFromPlaylist', methods=['PUT'])
def removeModulesFromPlaylist():
	if not 'username' in session:
		return jsonify(error = 'not logged in')
	if request.method == 'PUT':
		if not 'username' in session:
			return jsonify(error = 'Not logged in.')

		#try to obtain json data from frontend
		try:
			data = request.get_json()
			playlistID = data['playlistID']
			moduleList = data['modules']
		except KeyError as e:
			return jsonify('Invalid Input.')

		#check if you are allowed to modify this playlist
		playlist = Playlists.query.filter_by(id = playlistID).first()
		if playlist is None:
			return jsonify(error = 'Playlist does not exist.')
		if not isAdmin() and playlist.owner != session['username']:
			return jsonify(error = 'not privileged.')

		#does module exist?
		for moduleID in moduleList:
			#try to obtain the module
			module = Modules.query.filter_by(id = int(moduleID)).first()
			if module is None:
				print('Module does not exist, cant take it from playlist')
				continue

			#remove module from playlist
			playlist.modules.remove(module)
			db_alch.session.commit()

		return jsonify(result = 'confirmed')


#already ok
@app_rest.route('/_requestNewBuildFromPlaylist', methods=['POST'])
def requestNewBuildFromPlaylist():
	if not 'username' in session:
		return jsonify(error = 'not logged in')
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
			return jsonify(error= "Inavlid Input")


		if allUserImages.__len__() >= int(dbUser.max_images):
			return jsonify(error = 'You have reached your maximum limit of OpenStack Images.')

		if not checkings.checkToolAvailability():
			return jsonify(error = 'Some of the necessary automation tools are not available. Please contact the administrator.')

		playlistID = int(data['playlistID'])
		desiredJobName = data['jobName']
		#check if playlist exists
		playlist = Playlists.query.filter_by(id = playlistID).first()
		if playlist is None:
			return jsonify(error = 'No playlist with such id was found.')
		#check if playlist is yours or admin
		if playlist.owner != session['username'] and not isAdmin():
			return jsonify(error = 'Not privileged to use this playlist.')

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
def requestNewBuild():
	#todo I maybe have to put the debug messages into a list, instead of an concated string
	if not 'username' in session:
		return jsonify(error = 'not logged in')
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
			return jsonify(error='You have reached your maximum limit of OpenStack Images.')


		if not checkings.checkToolAvailability():
			return jsonify(error = 'Some of the necessary automation tools are not available. Please contact the administrator.')

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
@app_rest.route('/_uploadModule', methods=['POST'])
def uploadModule():
	MODULE_TYPE = 1
	MODULE_TYPE_DIRECTORY = 2
	if request.method == 'POST':
		print(request.form)
		print(request.files['file'])
		if not request.files['file']:
			return jsonify(error = "ERROR: No File has been sent to me.")
		file = request.files['file']
		tupleExtension = checkings.categorizeAndCheckModule(file)
		if tupleExtension[0] == 'N/A':
			return jsonify(error = "ERROR: Could not categorize file. Make sure it is supported and has the right extension")

		#check priviliges for forced modules, booleans from frontend are forced to strings
		isForced = 'false'
		if session['username'] == 'admin' and 'isForced' in request.form:
			if request.form['isForced'] == 'true' or request.form['isForced'] == 'false':
				isForced = request.form['isForced']


		formDataCheck = checkings.checkNewModuleForm(request.form)
		if not formDataCheck == 'okay':
			return jsonify(error = formDataCheck)



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
@app_rest.route('/_getHistory', methods = ['GET'])
def getHistory():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	#if admin, return every history made
	if session['username'] == 'admin':
		query = History.query.all()
		historyList = [i.serialize for i in query]
	else:
		query = History.query.filter_by(owner = session['username']).all()
		historyList = [i.serialize for i in query]
	return jsonify(historyList)

#tested
@app_rest.route('/_getPlaylists')
def getPlaylists():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	if isAdmin():
		query = Playlists.query.all()
		playlistList = [i.serialize for i in query]
	else:
		query = Playlists.query.filter_by(owner = session['username']).all()
		playlistList = [i.serialize for i in query]
	return jsonify(playlistList)


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
@app_rest.route('/_deletePlaylistByID/<int:targetID>', methods = ['DELETE'])
def deletePlaylistByID(targetID):
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')


	targetPlaylist = Playlists.query.filter_by(id = int(targetID)).first()
	if targetPlaylist is None:
		return jsonify(error = 'Playlist does not exist.')

	#check privileges
	if not isAdmin() and targetPlaylist.owner != session['username']:
		return jsonify(error = 'not privileged')

	db_alch.session.delete(targetPlaylist)
	db_alch.session.commit()
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

#tested
@app_rest.route('/_updatePlaylistDescription', methods=['PUT'])
def updatePlaylistDescription():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	if request.method == 'PUT':
		try:
			data = request.get_json()
			playlistID = data['playlistID']
			comment = data['description']
		except KeyError as e:
			return jsonify(error = 'Invalid Input.')
		#try to obtain desired playlist from db
		playlist = Playlists.query.filter_by(id = playlistID).first()
		if playlist is None:
			return jsonify(error = 'Playlist could not be found.')
		#check privileges
		if not isAdmin() and playlist.owner != session['username']:
			return jsonify(error='not privileged')
		playlist.description = comment
		db_alch.session.commit()
		return jsonify(result = 'confirmed')
	return jsonify('Illegal Method')



#tested
@app_rest.route('/_addModuleToPlaylist/<int:playlistID>/<int:moduleID>', methods=['PUT'])
def addModuleToPlaylist(playlistID, moduleID):
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	if request.method == 'PUT':

		#make some checks
		targetPlaylist = Playlists.query.filter_by(id = playlistID).first()
		targetModule = Modules.query.filter_by(id = moduleID).first()
		if targetPlaylist is None or targetModule is None:
			return jsonify(error = 'Playlist or module not found.')
		#check if user is allowed to modify this playlist
		if targetPlaylist.owner != session['username'] and not isAdmin():
			return jsonify(error = 'Not privileged (not your playlist).')

		if targetModule.owner != session['username'] and targetModule.isPrivate == 'false' and not isAdmin():
			return jsonify(error = 'Not privileged (not your module or not public).')

		#check if module is already in playlist
		playlistModules = targetPlaylist.modules
		for module in playlistModules:
			if int(module.id) == targetModule.id:
				return jsonify(result = "Already in playlist.")

		#all is set, add module to playlist
		targetPlaylist.modules.append(targetModule)
		db_alch.session.commit()
		return jsonify(result = 'Module has been added to playlist.')

#tested
@app_rest.route('/_addGalaxyRoleToPlaylist', methods=['POST'])
def addGalaxyRoleToPlaylist():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')

	if request.method == 'POST':
		data = request.get_json()
		try:
			playlistID = int(data['playlistID'])
			roleDescription = data['roleDescription']
			roleName = str(data['roleName'])
		except KeyError:
			return jsonify(error = 'invalid input.')

		targetPlaylist = Playlists.query.filter_by(id = playlistID).first()
		if targetPlaylist is None:
			return jsonify(error = 'Playlist not found.')
		#check if user is allowed to modify this playlist
		if targetPlaylist.owner != session['username'] and not isAdmin():
			return jsonify(error = 'Not privileged (not your playlist).')

		#check if module is already in playlist
		playlistModules = targetPlaylist.modules
		for module in playlistModules:
			if str(module.name) == roleName:
				return jsonify(result = "Already in playlist.")

		newGalaxyModule = Modules(roleName, session['username'], roleDescription, 'n/a', 'n/a', 'GALAXY', 'n/a', 'false')
		targetPlaylist.modules.append(newGalaxyModule)
		db_alch.session.commit()
		return jsonify(result = "Galaxy Role has been added to the playlist.")



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

#tested
@app_rest.route('/_getCrashLog/<int:targetID>', methods = ['GET'])
def getCrashLog(targetID):

	#get the job
	job = Jobs.query.filter_by(id = int(targetID)).first()
	if job is None:
		return jsonify(error = 'No job with such id was found')
	#check privileges
	if job.owner != session['username'] and not isAdmin():
		return jsonify(error = 'not privileged')
	#send the log
	filepath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/log.txt'
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
@app_rest.route('/_removeJobByID/<int:id>', methods=['DELETE'])
def removeJobByID(id):
	if request.method == 'DELETE':


		#obtain the job from db
		job = Jobs.query.filter_by(id = id).first()
		if job is None:
			return jsonify(error = 'Could not find job with this id.')

		#check privileges
		if job.owner != session['username'] and not isAdmin():
			return jsonify(error = 'Not privileged.')

		#check if its not running right now
		if job.status != 'ABORTED' and job.status != 'BUILD OKAY':
			return jsonify(error = 'Build is still running, wait for it to halt.')

		#otherwise kill it with fire
		directoryPath = constants.ROOT_PATH + constants.TMP_DIRECTORY + str(job.id) + '/'
		shutil.rmtree(directoryPath, ignore_errors=True)
		db_alch.session.delete(job)
		db_alch.session.commit()

		return jsonify(result = 'confirmed')

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


