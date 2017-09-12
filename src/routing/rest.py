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

#TODO: Refactor all SQL Query Statements
#TODO: Write config file for credentials or let mysql set in frontend.
DB_CREDENTIALS = ('localhost', 'root', 'master', 'bibicreator')


#Start main worker thread
thread = JobWorker(DB_CREDENTIALS)
thread.start()


#TODO: Make only accessible from admin
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
	userDict = {'userName' : request.args.get('userName', 0, type=str),
				'userPassword' : request.args.get('userPassword', 0, type=str),
				'userEmail' : request.args.get('userEmail', 0,  type=str),
				'userMax' : request.args.get('userMax', 0, type=str)}

	if checkings.checkPassedUserFormular(userDict):
		try:
			db = DB_Connector(*DB_CREDENTIALS)
			db.queryAndResult('INSERT INTO Users (id, name, password, policy, max_images, email) VALUES (NULL, %s, %s, %s, %s, %s)',
							  (userDict['userName'],
							  userDict['userPassword'],
							  'user',
							  userDict['userMax'],
							  userDict['userEmail']))
			db.db.commit()
			return jsonify(result = 'confirmed')
		except IntegrityError as e:
			code, msg = e.args
			return jsonify(result = str(code))

@app_rest.route('/_updateUser')
def updateUser():
	#first get actual user data
	manipulatedUserID = str(request.args.get('userID', 0, type=int))
	manipulatedPassword = request.args.get('password', 0, type=str)
	manipulatedEmail = request.args.get('email', 0, type=str)
	manipulatedMaxInstances = request.args.get('max_instances', 0, type=str)
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		originalData = db.queryAndResult('SELECT password, email, max_images FROM Users WHERE id=%s', manipulatedUserID)
		#TODO Check if result is okay if not called by frontend
		if not manipulatedPassword:
			db.queryAndResult('UPDATE Users SET email = %s , max_images = %s WHERE Users.id = %s',
							  (manipulatedEmail, manipulatedMaxInstances, manipulatedUserID))
			db.db.commit()
			return jsonify(result = 'confirmed')
		db.queryAndResult('UPDATE Users SET password = %s , email = %s , max_images = %s WHERE Users.id = %s',
						  (manipulatedPassword, manipulatedEmail, manipulatedMaxInstances, manipulatedUserID))
		db.db.commit()
		return jsonify(result = 'confirmed')
	except IntegrityError as e:
		code, msg = e.args
		return jsonify(result = str(code))

@app_rest.route('/_getOwnModules')
def getOwnModules():
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		result = db.queryAndResult('SELECT id, name, owner, isPrivate, module_type, version, date FROM Modules WHERE owner = %s ORDER BY date DESC',
								   (session['username']))
		return jsonify(result)
	except Exception as e:
		return jsonify('N/A')

@app_rest.route('/_getPublicModules')
def getPublicModules():
	try:
		#todo Give an admin every module, indendent from privacy
		db = DB_Connector(*DB_CREDENTIALS)
		result = db.queryAndResult('SELECT id, name, owner, isPrivate, module_type, version, date FROM Modules WHERE NOT owner = %s AND isPrivate = "false" AND isForced = "false" ORDER BY date DESC',
								   (session['username']))
		return jsonify(result)
	except Exception as e:
		return jsonify('N/A')

@app_rest.route('/_getModuleByID')
def getModuleByID():
	try:
		targetID = request.args.get('id', 0, type=str)
		db = DB_Connector(*DB_CREDENTIALS)
		result = db.queryAndResult('SELECT id, name, owner, description, version, date, module_type, isPrivate, isForced FROM Modules WHERE id = %s ',
								   (targetID))[0]
		return jsonify(result)
	except Exception as e:
		return jsonify('N/A')

@app_rest.route('/_getJobs')
def getJobs():
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		if session['username'] == 'admin':
			result = db.queryAndResult('SELECT * FROM Jobs ORDER BY date DESC', None)
		else:
			result = db.queryAndResult('SELECT * FROM Jobs WHERE owner = %s ORDER BY date DESC', session['username'])
		returnList = []
		for row in result:
			dictResult = {'id': row[0],
						  'owner': row[1],
						  'name': row[2],
						  'status': row[3],
						  'progress': row[4],
						  'debug_file_path': row[5],
						  'base_image_id': row[6],
						  'new_image_id': row[7],
						  'date': row[8]}
			returnList.append(dictResult)
		return jsonify(returnList)



	except Exception as e:
		print(e)


@app_rest.route('/_getForcedModules')
def getForcedModules():
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		result = db.queryAndResult('SELECT id, name, owner, isPrivate, module_type, version, date FROM Modules WHERE isForced = "true" ORDER BY date DESC',None)
		return jsonify(result)
	except Exception as e:
		return jsonify('N/A')

@app_rest.route('/_deleteModuleByID')
def deleteModuleByID():
	#only admin or own owner can delete modules
	#obtain the targeted entry in mysql to make some privilege checks
	#todo delete module files from disk as well?
	targetID = request.args.get('id', 0, type=str)
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		result = db.queryAndResult('SELECT owner, path FROM Modules WHERE id = %s', (targetID))
		print(result)
		if session['username'] == 'admin' or result[0][0] == session['username']:
			db.queryAndResult('DELETE FROM Modules WHERE id = %s', targetID)
			db.db.commit()
			return jsonify(result = "confirmed")
		return jsonify(result = "not allowed")
	except Exception as e:
		return jsonify('N/A')
	pass

@app_rest.route('/_getFileByID')
def getFileByID():
	#todo add policy rules
	targetID = request.args.get('id', 0, type=str)
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		result = db.queryAndResult('SELECT path FROM Modules WHERE id = %s', targetID)[0]
		filepath = constants.ROOT_PATH + '/' + result[0]
		print("Got as filepath: " + filepath)
		return send_file(filepath, as_attachment=True, mimetype='text/plain')
	except Exception as e:
		print(e)
		return jsonify("N/A")


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
		try:
			db = DB_Connector(*DB_CREDENTIALS)
			queryResult = db.queryAndResult('SELECT name FROM Jobs WHERE name=%s', desiredJobName)
			if queryResult.__len__() != 0:
				debugMsg = debugMsg + "\n ERROR: Job Name already exists."
				return jsonify(result = ['error', debugMsg])

			#check if module entrys are valid by checking permissions and ownership of the modules
			for moduleID in moduleList:
				queryResult = db.queryAndResult('SELECT owner, isPrivate FROM Modules WHERE id=%s', moduleID)[0]
				if queryResult is None:
					moduleList.remove(moduleID)
					debugMsg = debugMsg + "\n WARNING: There is no module with the id " + moduleID + " in the Database!"
					continue
				#is the current user allowed to use the module?
				if queryResult[0] != user and user != 'admin' and queryResult[1] == 'false':
					moduleList.remove(moduleID)
					debugMsg = debugMsg + "\n This user is not allowed to use module id " + moduleID
					continue
			print("Cleaned module list contains: " + str(moduleList))
			#todo checke user max limit

			#build job in database
			db.queryAndResult('INSERT INTO Jobs (id, owner, name, status, progress, base_image_id, date) VALUES (NULL, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP )',
							  (session['username'],
							   desiredJobName,
							   'NEW',
							   'not_started',
							   '57df71b5-b446-46ac-8094-80970488454c'))
			db.db.commit()

			#fetch id from freshly created job
			jobID = db.queryAndResult('SELECT id FROM Jobs WHERE name=%s', desiredJobName)[0][0]

			#fill jobs_modules
			for moduleID in moduleList:
				db.queryAndResult('INSERT INTO jobs_modules (id_jobs, id_modules) VALUES (%s, %s)', (jobID, moduleID))

			db.db.commit()
			#let the db digest all of this
			sleep(3)
			debugMsg = debugMsg + "\n Your Job has been created!"
			return jsonify(result = ['confirmed', debugMsg])



		except IntegrityError as e:
			print(e)
			debugMsg = debugMsg + "\n FATAL: Error in database, I won't show you the error, either you found a bug or you tried to break in....Anzeige ist raus."
			return jsonify(result = ['error', debugMsg])


	#todo extend this result to a hyperlink?
	return jsonify(result = ['confirmed', 'Your job has been created!'])

@app_rest.route('/_uploadModule', methods=['POST'])
def uploadModule():
	MODULE_TYPE = 1
	MODULE_TYPE_DIRECTORY = 2
	if request.method == 'POST':
		if not request.files['file']:
			return jsonify(result = "ERROR: No File has been sent to me.")
		file = request.files['file']
		tupleExtension = checkings.categorizeAndCheckModule(file)
		if tupleExtension[0] == 'N/A':
			return jsonify(result = "ERROR: Could not categorize file. Make sure it is supported and has the right extension")

		#check priviliges for forced modules, booleans from frontend are forced to strings
		isForced = 'false'
		if session['username'] == 'admin' and request.form['isForced'] == 'true':
			isForced = 'true'


		formDataCheck = checkings.checkNewModuleForm(request.form)
		if not formDataCheck == 'okay':
			return jsonify(result = formDataCheck)

		timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')
		dbFileName = session['username'] +timestamp + file.filename
		try:
			db = DB_Connector(*DB_CREDENTIALS)
			db.queryAndResult('INSERT INTO Modules (id, name, owner, description, version, isPrivate, module_type, path, isForced, date) VALUES (NULL , %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP )',
							  (request.form['moduleName'],
							   session['username'],
							   request.form['moduleDescriptionText'],
							   request.form['moduleVersion'],
							   request.form['isPrivate'],
							   tupleExtension[MODULE_TYPE],
							   tupleExtension[MODULE_TYPE_DIRECTORY] + '/' + dbFileName,
							   isForced))
			db.db.commit()
			file.save(os.path.join(constants.ROOT_PATH + '/' + tupleExtension[MODULE_TYPE_DIRECTORY], secure_filename(dbFileName)))
		except IntegrityError as e:
			return jsonify(result = e)

	return jsonify(result = 'confirmed')




###########ALCHEMY TESTS########################



@app_rest.route('/_test')
def alchemytest():
	user = Users.query.filter_by(name='admin').first()
	return jsonify(user.name)





