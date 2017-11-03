
import re
import os
from datetime import datetime
from time import sleep
import subprocess

from flask import Blueprint, request, jsonify, send_file
from pymysql import IntegrityError
from werkzeug.utils import secure_filename

from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.utils import local_resource, checkings, constants
import shutil
import tarfile


app_rest = Blueprint('app_rest', __name__)

#TODO: Write config file for credentials or let mysql set in frontend.
DB_CREDENTIALS = ('localhost', 'root', 'master', 'bibicreator')



def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False



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

@app_rest.route('/_getVersions')
def getVersions():
	dictV = {}
	dictV['ansible'] = local_resource.get_app_version('ansible --version | head -n 1')
	dictV['packer'] = local_resource.get_app_version('./packer version')
	dictV['db'] = local_resource.get_app_version('mysql --version')
	return jsonify(dictV)

@app_rest.route('/_getUsers')
def getUsers():
	if 'username' in session and session['username'] == 'admin':
		sqlquery = Users.query.all()
		return jsonify([i.serialize for i in sqlquery])
	return jsonify(error = 'not privileged')

@app_rest.route('/_deleteUser')
def deleteUser():
	userID = request.args.get('id', 0, type=str)
	print("Got a user id I have to delete: " + userID)
	if userID == '1':
		print('Cant delete Admin Account....like cutting off an own leg :( ')
		return jsonify(0)
	try:
		targetUserID = Users.query.filter_by(id=int(userID)).first()
		if targetUserID is None:
			return jsonify(result= 'no user with such id was found.')

		#actual delete process
		Users.query.filter_by(id=int(userID)).delete()
		db_alch.session.commit()

		return jsonify(result = 'confirmed')
	except Exception as e:
		print(e)
	return jsonify(0)

@app_rest.route('/_createUser')
def createUser():
	if not isAdmin():
		return jsonify(error='not privileged')

	userDict = {'userName' : request.args.get('userName', 0, type=str),
				'userPassword' : request.args.get('userPassword', 0, type=str),
				'userEmail' : request.args.get('userEmail', 0,  type=str),
				'userMax' : request.args.get('userMax', 0, type=str)}

	if checkings.checkPassedUserFormular(userDict):
		try:
			new_user = Users(userDict['userName'], userDict['userPassword'], userDict['userMax'], userDict['userEmail'])
			db_alch.session.add(new_user)
			db_alch.session.commit()
			return jsonify(result = 'confirmed')
		except IntegrityError as e:
			code, msg = e.args
			return jsonify(result = str(code))


@app_rest.route('/_changeUserPassword', methods=['POST'])
def changeUserPassword():

	if 'username' not in session:
		return jsonify(error = 'Not logged in')

	if request.method == 'POST':

		data = request.get_json()
		if not all(k in data for k in ('oldPassword', 'newPassword', 'repeatNewPassword')):
			return jsonify(error = 'Invalid Input.')

		#check if oldPassword matches
		user = Users.query.filter_by(name = session['username']).first()
		if user.password != data['oldPassword']:
			return jsonify(error = 'Old password does not match.')

		if str(data['newPassword']).__len__() <= 4:
			return jsonify(error = 'Password is too short, at least 5 character!')

		if data['newPassword'] != data['repeatNewPassword']:
			return jsonify(error = 'New password is not the same is the repeated password!')

		#set the new password in db
		#todo enrypt this part
		user.password = data['newPassword']
		db_alch.session.commit()
		session['logged_in'] = False
		session.pop(session['username'], None)
		return jsonify(result = 'Confirmed.')
	return jsonify(error = 'Not allowed.')





@app_rest.route('/_updateUser', methods=['POST'])
def updateUser():
	if 'username' not in session:
		return jsonify(error = 'Not logged in.')
	if not isAdmin():
		return jsonify(error = 'Not privileged.')





	#first get actual user data
	manipulatedUserID = str(request.args.get('userID', 0, type=int))
	manipulatedPassword = request.args.get('password', None, type=str)
	manipulatedEmail = request.args.get('email', 0, type=str)
	manipulatedMaxInstances = request.args.get('max_instances', 0, type=str)
	try:

		userRow = Users.query.filter_by(id = int(manipulatedUserID)).first()
		if userRow is None:
			return jsonify(error = 'can\'t update user, does not exist.')

		print(type(manipulatedPassword))
		if manipulatedPassword is not '':
			userRow.password = manipulatedPassword
		userRow.email = manipulatedEmail
		userRow.max_images = manipulatedMaxInstances

		db_alch.session.commit()
		return jsonify(result = 'confirmed')
	except IntegrityError as e:
		code, msg = e.args
		return jsonify(result = str(code))

@app_rest.route('/_getOwnModules')
def getOwnModules():
	try:
		moduleList = Modules.query.filter_by(owner = session['username'], isForced = 'false').filter(Modules.module_type != 'GALAXY').all()
		return jsonify([i.serialize for i in moduleList])
	except Exception as e:
		return jsonify('N/A')

@app_rest.route('/_getPublicModules')
def getPublicModules():
	if 'username' not in session:
		return jsonify(error = "not logged in.")

	#If the current user is the admin, give him EVERY Module from EVERY User
	if session['username'] == 'admin':
		moduleList = Modules.query.filter(Modules.owner != 'admin').all()
	#If current user is not the admin, send only modules which are set to public
	else:
		moduleList = Modules.query.filter((Modules.owner != session['username']), (Modules.isPrivate == 'false')).all()
	return jsonify([i.serialize for i in moduleList])


@app_rest.route('/_getModuleByID')
def getModuleByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	#todo check if input is valid
	targetID = request.args.get('id', 0, type=str)

	targetModule = Modules.query.filter_by(id = int(targetID)).first()
	if targetModule is None:
		return jsonify(error = 'there is no module with such id.')

	return jsonify(targetModule.serialize)


@app_rest.route('/_getJobs')
def getJobs():
	if not 'username' in session:
		return jsonify(error = 'not privileged')

	if session['username'] == 'admin':
		jobList = Jobs.query.all()
	else:
		jobList = Jobs.query.filter_by(owner = session['username']).all()

	return jsonify([i.serialize for i in jobList])


@app_rest.route('/_getForcedModules')
def getForcedModules():
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	forcedModulesList = Modules.query.filter_by(isForced = 'true').all()
	return jsonify([i.serialize for i in forcedModulesList])


@app_rest.route('/_deleteModuleByID')
def deleteModuleByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	targetID = request.args.get('id', 0, type=str)
	#try to find a module with this id an obtain an object
	toBeDeletedModule = Modules.query.filter_by(id = int(targetID)).first()
	if toBeDeletedModule is None:
		return jsonify(error = 'There is no module with the id: ' + str(targetID))

	#a module can be deleted if done by admin or by the owner of the module
	if session['username'] == 'admin' or toBeDeletedModule.owner == session['username']:
		Modules.query.filter_by(id = toBeDeletedModule.id).delete()
		db_alch.session.commit()
		return jsonify(result = 'confirmed')
	else:
		return jsonify(error = 'not privileged to delete module.')


@app_rest.route('/_deleteOSImageByName', methods=['POST'])
def deleteOSImageByName():
	if not 'username' in session:
		return jsonify(error = 'not logged in.')

	if request.method == 'POST':
		data = request.get_json()
		if not 'imageName' in data:
			return jsonify(error = 'Invalid Input.')
		if isAdmin():
			images = constants.OS_CONNECTION.getAllBibiCreatorImages()
		else:
			images = constants.OS_CONNECTION.getBibiCreatorImagesByUser(session['username'])
		for image in images:
			if image.name == data['imageName']:
				constants.OS_CONNECTION.deleteImageByName(image.name)
				return jsonify(result = 'confirmed')
		return jsonify(error = 'could not find image with such name.')

	return jsonify(error = 'Invalid Method.')




@app_rest.route('/_getFileByID')
def getFileByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetID = request.args.get('id', 0, type=str)

	#get the desired module row
	targetModule = Modules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged')

	filepath = constants.ROOT_PATH + '/' + targetModule.path
	return send_file(filepath, as_attachment=True, mimetype='text/plain')


@app_rest.route('/_registerNewPlaylist', methods=['POST'])
def registerNewPlaylist():
	if request.method == 'POST':
		data = request.get_json()
		print(data)
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
@app_rest.route('/_removeModulesFromPlaylist', methods=['POST'])
def removeModulesFromPlaylist():
	if request.method == 'POST':
		if not 'username' in session:
			return jsonify(error = 'Not logged in.')

		#try to obtain json data from frontend
		try:
			data = request.get_json()
			print(data)
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


@app_rest.route('/_requestNewBuildFromPlaylist', methods=['POST'])
def requestNewBuildFromPlaylist():
	if request.method == 'POST':
		debugMsg = ''
		data = request.get_json()
		user = session['username']
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
			if fetchedModule.owner != user and user != 'admin' and fetchedModule.isPrivate == 'false':
				moduleList.remove(moduleID)
				debugMsg = debugMsg + "\n This user is not allowed to use module id " + moduleID
				continue

		# build job in database
		newJob = Jobs(desiredJobName, session['username'], 'NEW', 'not_started', None,
					  '57df71b5-b446-46ac-8094-80970488454c', None)
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



@app_rest.route('/_requestNewBuild', methods=['POST'])
def requestNewBuild():
	#todo I maybe have to put the debug messages into a list, instead of an concated string
	if request.method == 'POST':
		debugMsg = ''
		data = request.get_json()
		moduleList = data['modules']
		desiredJobName = data['name']
		#remove duplicates
		moduleList = list(set(moduleList))
		#verify that this is a valid moduleList
		user = session['username']

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
			if fetchedModule.owner != user and user != 'admin' and fetchedModule.isPrivate == 'false':
				moduleList.remove(moduleID)
				debugMsg = debugMsg + "\n This user is not allowed to use module id " + moduleID
				continue

		#build job in database
		newJob = Jobs(desiredJobName, session['username'], 'NEW', None, '57df71b5-b446-46ac-8094-80970488454c', None)
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

@app_rest.route('/_uploadModule', methods=['POST'])
def uploadModule():
	MODULE_TYPE = 1
	MODULE_TYPE_DIRECTORY = 2
	if request.method == 'POST':
		if not request.files['file']:
			return jsonify(error = "ERROR: No File has been sent to me.")
		file = request.files['file']
		tupleExtension = checkings.categorizeAndCheckModule(file)
		if tupleExtension[0] == 'N/A':
			return jsonify(error = "ERROR: Could not categorize file. Make sure it is supported and has the right extension")

		#check priviliges for forced modules, booleans from frontend are forced to strings
		isForced = 'false'
		if session['username'] == 'admin' and request.form['isForced'] == 'true':
			isForced = 'true'


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



@app_rest.route('/_getHistory')
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



@app_rest.route('/_deleteHistoryByID')
def deleteHistoryByID():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	targetID = request.args.get('id', 0, type=str)
	#try to obtain this desired history from the db
	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'No History found with this id.')

	#check privileges
	if session['username'] != 'admin' or targetHistory.owner != session['username']:
		return jsonify(error = 'not privileged')

	db_alch.session.delete(targetHistory)
	db_alch.session.commit()
	shutil.rmtree(constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id), ignore_errors=True)
	return jsonify(result = 'confirmed')


@app_rest.route('/_deletePlaylistByID')
def deletePlaylistByID():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	targetID = request.args.get('id', 0, type=str)

	targetPlaylist = Playlists.query.filter_by(id = int(targetID)).first()
	if targetPlaylist is None:
		return jsonify(error = 'Playlist does not exist.')

	#check privileges
	if not isAdmin() or targetPlaylist.owner != session['username']:
		return jsonify(error = 'not privileged')

	db_alch.session.delete(targetPlaylist)
	db_alch.session.commit()
	return jsonify(result = 'confirmed')



@app_rest.route('/_updateHistoryComment', methods=['POST'])
def updateHistoryComment():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	if request.method == 'POST':
		data = request.get_json()
		#try to obtain this desired history from the db
		targetHistory = History.query.filter_by(id = int(data['targetID'])).first()
		if targetHistory is None:
			return jsonify(error = 'No History found with this id.')
		#check privileges
		if session['username'] != 'admin' or targetHistory.owner != session['username']:
			return jsonify(error = 'not privileged')
		targetHistory.commentary = data['commentary']
		db_alch.session.commit()
		return jsonify(result = 'confirmed')
	return jsonify(error = 'Unknown Error.')


@app_rest.route('/_updatePlaylistDescription', methods=['POST'])
def updatePlaylistDescription():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	if request.method == 'POST':
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




@app_rest.route('/_addModuleToPlaylist', methods=['POST'])
def addModuleToPlaylist():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')
	if request.method == 'POST':
		data = request.get_json()
		try:
			playlistID = int(data['playlistID'])
			moduleID = int(data['moduleID'])
		except KeyError as e:
			return jsonify(error = 'Illegal input. Aborting.')
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





#todo this is still request based
@app_rest.route('/_getHistoryLogByID')
def getHistoryLogByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetID = request.args.get('id', 0, type=str)
	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetHistory.owner != session['username'] and targetHistory.isPrivate == 'false':
		return jsonify(error = 'not privileged')


	filepath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id) + '/log.txt'
	#print('trying to send file {}'.format(filepath))
	return send_file(filepath, as_attachment=True, mimetype='text/plain')


@app_rest.route('/_getCrashLog')
def getCrashLog():

	targetID = request.args.get('id', 0, type=str)


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




@app_rest.route('/_getBackupHistoryByID')
def getBackupHistoryByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetID = request.args.get('id', 0, type=str)
	targetHistory = History.query.filter_by(id = int(targetID)).first()

	if targetHistory is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetHistory.owner != session['username'] and targetHistory.isPrivate == 'false':
		return jsonify(error = 'not privileged')


	filepath = constants.ROOT_PATH + constants.HISTORY_DIRECTORY + str(targetHistory.id) + '/backup.tar.gz'
	print('trying to send file {}'.format(filepath))
	return send_file(filepath, as_attachment=True, mimetype='application/gzip')

@app_rest.route('/_getHistoryModuleByID')
def getHistoryModuleByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetID = request.args.get('id', 0, type=str)
	targetModule = HistoryModules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged')

	return jsonify(targetModule.serialize)


@app_rest.route('/_getHistoryModuleFileByID')
def getHistoryModuleFileByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in')

	targetID = request.args.get('id', 0, type=str)
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



@app_rest.route('/_removeJobByID', methods=['POST'])
def removeJobByID():
	if request.method == 'POST':
		data = request.get_json()

		if not 'id' in data:
			return jsonify(error = 'No id was given.')

		#obtain the job from db
		job = Jobs.query.filter_by(id = int(data['id'])).first()
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

@app_rest.route('/_changeBaseImgByID', methods=['POST'])
def changeBaseImgByID():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.')

	if not isAdmin():
		return jsonify(error = 'Not privileged.')

	if request.method == 'POST':
		data = request.get_json()
		constants.CONFIG.os_base_img_id = data['imgId']
		return jsonify(result = 'confirmed')





###########ALCHEMY TESTS########################


@app_rest.route('/_test')
def testroute():
	print(constants.CONFIG.os_base_img_id)
	constants.CONFIG.os_base_img_id = '09567453-48e5-4e8e-a32b-56069a945f0e'


	return jsonify(bla = 'suppe')


