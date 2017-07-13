from flask import Blueprint, render_template, flash, request, session, jsonify
from pymysql import IntegrityError

from src.utils import  local_resource, checkings
from src.utils.db_connector import DB_Connector

app_rest = Blueprint('app_rest', __name__)

#TODO: Write config file for credentials or let mysql set in frontend.
DB_CREDENTIALS = ('localhost', 'root', 'master', 'bibicreator')

#TODO: Make only accessible from admin
@app_rest.route('/_getHealth')
def getHealth():
	randomDict = {'cpu_name' : local_resource.get_processor_name(),
				  'cpu_load' : local_resource.get_cpu_load(),
				  'ram_usage': local_resource.get_ram_percent()}
	return jsonify(randomDict)

@app_rest.route('/_getVersions')
def getVersions():
	dictV = {}
	dictV['ansible'] = local_resource.get_app_version('ansible --version | head -n 1')
	dictV['packer'] = local_resource.get_app_version('./packer version')
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		dictV['db'] = db.queryAndResult('SELECT VERSION()', None)[0]
	except Exception as e:
		print(e)
		dictV['db'] = 'N/A'
	return jsonify(dictV)

@app_rest.route('/_getUsers')
def getUsers():
	main_dictV = {}
	try:
		db = DB_Connector(*DB_CREDENTIALS)
	except Exception as e:
		print(e)
		return jsonify('N/A')
	result = db.queryAndResult('SELECT id, name, policy, max_images, email FROM Users', None)
	#print(result)
	return jsonify(result)

@app_rest.route('/_deleteUser')
def deleteUser():
	userID = request.args.get('id', 0, type=str)
	print("Got a user id I have to delete: " + userID)
	if userID == '1':
		print('Cant delete Admin Account....like cutting off an own leg :( ')
		return jsonify(0)
	try:
		db = DB_Connector('localhost', 'root', 'master', 'bibicreator')
		db.queryAndResult('DELETE FROM Users WHERE id=%s',userID)
		db.db.commit()
		#flash('Delete confirmed.')
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
	#MAGIC NUMBER CONVERSION
	PASSWORD = 0
	EMAIL = 1
	MAX_IMAGES = 2
	#first get actual user data
	manipulatedUserID = str(request.args.get('userID', 0, type=int))
	manipulatedPassword = request.args.get('password', 0, type=str)
	manipulatedEmail = request.args.get('email', 0, type=str)
	manipulatedMaxInstances = request.args.get('max_instances', 0, type=str)
	print('max instances: ' + manipulatedMaxInstances)
	print("Attempting to manipulate user with id: " + manipulatedUserID)
	try:
		db = DB_Connector(*DB_CREDENTIALS)
		changePassword = True
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

