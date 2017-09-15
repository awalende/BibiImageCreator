import os
from datetime import datetime
from time import sleep

from flask import Blueprint, request, jsonify, send_file
from pymysql import IntegrityError
from werkzeug.utils import secure_filename

from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.threads.workerThread import JobWorker
from src.utils import local_resource, checkings, constants
from src.utils.db_connector import DB_Connector

app_rest = Blueprint('app_rest', __name__)

#TODO: Write config file for credentials or let mysql set in frontend.
DB_CREDENTIALS = ('localhost', 'root', 'master', 'bibicreator')


#Start main worker thread
#thread = JobWorker(db_alch)
#thread.start()


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

@app_rest.route('/_updateUser')
def updateUser():
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
		moduleList = Modules.query.filter_by(owner = session['username'], isForced = 'false').all()
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



@app_rest.route('/_getFileByID')
def getFileByID():
	if not 'username' in session:
		return jsonify(error = 'not logged in')


	#todo add policy rules
	targetID = request.args.get('id', 0, type=str)

	#get the desired module row
	targetModule = Modules.query.filter_by(id = int(targetID)).first()

	if targetModule is None:
		return jsonify(error = 'not found')

	if session['username'] != 'admin' and targetModule.owner != session['username'] and targetModule.isPrivate == 'false':
		return jsonify(error = 'not privileged')

	filepath = constants.ROOT_PATH + '/' + targetModule.path
	return send_file(filepath, as_attachment=True, mimetype='text/plain')



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
		newJob = Jobs(desiredJobName, session['username'], 'NEW', 'not_started', None, '57df71b5-b446-46ac-8094-80970488454c', None)
		db_alch.session.add(newJob)
		db_alch.session.commit()

		#obtain the freshly created job object
		newJob = Jobs.query.filter_by(name = desiredJobName).first()

		#now fill the modules to the job
		for moduleID in moduleList:
			targetModule = Modules.query.filter_by(id = int(moduleID)).first()
			newJob.modules.append(targetModule)
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




###########ALCHEMY TESTS########################

#teste wie ich module zu jobs hinzufuegen kann

@app_rest.route('/_test1')
def testdb():
	job = Jobs.query.filter_by(id = 18).first()

	toBeAddedModule = Modules.query.filter_by(id = 23).first()
	print('Now trying to add module {} to job {}'.format(toBeAddedModule, job))

	print('Job has following modules: {}'.format(job.modules))

	job.modules.append(toBeAddedModule)
	db.session.commit()
	print('Now we have more modules? {}'.format(job.modules))





