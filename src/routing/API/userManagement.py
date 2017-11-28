from flasgger import swag_from
from flask import Blueprint, request, jsonify, send_file, current_app
from src.routing.views import session
from src.sqlalchemy.db_alchemy import db as db_alch
from src.sqlalchemy.db_model import *
from src.utils import constants
from src.utils import local_resource, checkings, constants
from pymysql import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

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
	if userID == 1:
		print('Cant delete Admin Account....like cutting off an own leg :( ')
		return jsonify(0)
	try:
		targetUserID = Users.query.filter_by(id=userID).first()
		if targetUserID is None:
			return jsonify(error= 'no user with such id was found.'), 404

		#actual delete process
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
				return jsonify(error = 'Invalid Input.'), 400
	return jsonify(error = 'Invalid Input'), 400


#tested
@app_rest.route('/_changeUserPassword', methods=['PUT'])
@swag_from('yamldoc/changeUserPassword.yaml')
def changeUserPassword():
	if 'username' not in session:
		return jsonify(error = 'Not logged in'), 401

	if request.method == 'PUT':

		data = request.get_json()
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
		user.password = generate_password_hash(data['newPassword'])
		db_alch.session.commit()
		session['logged_in'] = False
		session.pop(session['username'], None)
		return jsonify(result = 'Confirmed.')
	return jsonify(error = 'Not allowed.')