'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
'''

from flasgger import swag_from
from flask import Blueprint, request, jsonify, send_file, current_app
from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.utils import constants
from src.utils import local_resource, checkings, constants
from pymysql import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash


"""This module lists all REST calls for usermanagement.
Documentation for these functions are created by swagger in apidocs/
"""

app_rest = Blueprint('userManagement', __name__)

def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False



#tested
@app_rest.route('/_getUsers')
@swag_from('yamldoc/getUsers.yaml')
def getUsers():
	if 'username' in session and session['username'] == 'admin':
		#we send out all users to the admin
		sqlquery = Users.query.all()
		return jsonify([i.serialize for i in sqlquery])
	return jsonify(error = 'not privileged'), 401


#tested
#used in user_management.html
@app_rest.route('/_deleteUser/<int:userID>', methods = ['DELETE'])
@swag_from('yamldoc/deleteUser.yaml')
def deleteUser(userID):
	if not isAdmin():
		return jsonify(error = 'Not authorized'), 401
	print("Got a user id I have to delete: " + str(userID))
	#only admin has user id 1
	if userID == 1:
		print('Cant delete Admin Account....like cutting off an own leg :( ')
		return jsonify(0)
	try:
		#find the user with his id
		targetUserID = Users.query.filter_by(id=userID).first()
		if targetUserID is None:
			return jsonify(error= 'no user with such id was found.'), 404

		#actual delete the user from database
		Users.query.filter_by(id=userID).delete()
		db_alch.session.commit()

		return jsonify(result = 'confirmed')
	except Exception as e:
		print(e)
	return jsonify(0)


#tested
@app_rest.route('/_createUser', methods = ['POST'])
@swag_from('yamldoc/createUser.yaml')
def createUser():
	if not isAdmin():
		return jsonify(error='not privileged'), 401
	if request.method == 'POST':
		userDict = request.get_json()
		#check if the passed formular has the correct format (password length, email syntax)
		if checkings.checkPassedUserFormular(userDict):
			try:
				#build a new user db object and add it to db
				new_user = Users(userDict['userName'], generate_password_hash(userDict['userPassword']), userDict['userMax'], userDict['userEmail'])
				db_alch.session.add(new_user)
				db_alch.session.commit()
				return jsonify(result = 'confirmed')
			except IntegrityError as e:
				code, msg = e.args
				return jsonify(result = str(code))
			except KeyError:
				return jsonify(error = 'Invalid Input.'), 400
	return jsonify(error = 'Invalid Input'), 400


#tested
@app_rest.route('/_changeUserPassword', methods=['PUT'])
@swag_from('yamldoc/changeUserPassword.yaml')
def changeUserPassword():
	if 'username' not in session:
		return jsonify(error = 'Not logged in'), 401

	if request.method == 'PUT':
		#get old password and new password from html formular
		data = request.get_json()
		#if one of the needed fields is missing, abort mission.
		if not all(k in data for k in ('oldPassword', 'newPassword', 'repeatNewPassword')):
			return jsonify(error = 'Invalid Input.'), 400

		#check if oldPassword matches
		user = Users.query.filter_by(name = session['username']).first()
		if not check_password_hash(user.password, data['oldPassword']):
			return jsonify(error = 'Old password does not match.'), 400

		if str(data['newPassword']).__len__() <= 4:
			return jsonify(error = 'Password is too short, at least 5 character!'), 400

		if data['newPassword'] != data['repeatNewPassword']:
			return jsonify(error = 'New password is not the same is the repeated password!'), 400

		#set the new password in db
		#hash the new password
		user.password = generate_password_hash(data['newPassword'])
		db_alch.session.commit()
		session['logged_in'] = False
		#for safety reasons, log out
		session.pop(session['username'], None)
		return jsonify(result = 'Confirmed.')
	return jsonify(error = 'Not allowed.')


#tested
@app_rest.route('/_updateUser', methods=['PUT'])
@swag_from('yamldoc/updateUser.yaml')
def updateUser():
	if 'username' not in session:
		return jsonify(error = 'Not logged in.'), 401
	if not isAdmin():
		return jsonify(error = 'Not privileged.'), 401

	if request.method == 'PUT':
		#first get actual user data from frontend
		data = request.get_json()
		try:
			#check if the desired user target exists
			userRow = Users.query.filter_by(id = int(data['userID'])).first()
			if userRow is None:
				return jsonify(error = 'can\'t update user, does not exist.'), 404

			#dont change the password if there is now sent new password.
			if 'password' in data:
				if not data['password'] == '':
					userRow.password = generate_password_hash(data['password'])

			if 'email' in data:
				if not data['email'] == '':
					userRow.email = data['email']

			if 'max_instances' in data:
				if not data['max_instances'] == '':
					userRow.max_images = data['max_instances']

			#update database with the new set data
			db_alch.session.commit()
			return jsonify(result = 'confirmed')
		except IntegrityError as e:
			code, msg = e.args
			return jsonify(result = str(code)), 400



#tested
@app_rest.route('/_getUserImageLimit', methods = ["GET"])
@swag_from('yamldoc/getUserImageLimit.yaml')
def getUserImageLimit():
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401

	#query the user
	dbUser = Users.query.filter_by(name = session['username']).first()
	maxLimit = dbUser.max_images
	#get current usage from openstack
	try:
		if isAdmin():
			images = constants.OS_CONNECTION.getAllBibiCreatorImages()
		else:
			images = constants.OS_CONNECTION.getBibiCreatorImagesByUser(session['username'])
	except Exception as e:
		return jsonify(error = 'could not connect to openstack'), 400
	#count the images the user already has
	currentUsage = len(images)
	return jsonify({'currentUsage': currentUsage, 'maxLimit' : maxLimit})