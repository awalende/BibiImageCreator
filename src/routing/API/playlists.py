'''This module lists all REST calls for playlists.
Documentation for these functions are created by swagger in apidocs/
You should use the interactive swagger documentation, hence it provides more and better documentation.
For the swagger documentation, simply start BibiCreator and point your browser to <URL>/apidocs
'''


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



app_rest = Blueprint('playlists', __name__)

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
@app_rest.route('/_getPlaylists')
@swag_from('yamldoc/getPlaylists.yaml')
def getPlaylists():
	"""API Endpoint: Returns all playlists the user has saved. If run by administrator, all playlists in the system will be retreived.

	Returns:
		A JSON object containing a list of all user playlists.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401
	if isAdmin():
		query = Playlists.query.all()
		playlistList = [i.serialize for i in query]
	else:
		query = Playlists.query.filter_by(owner = session['username']).all()
		playlistList = [i.serialize for i in query]
	return jsonify(playlistList)


#tested
@app_rest.route('/_deletePlaylistByID/<int:targetID>', methods = ['DELETE'])
@swag_from('yamldoc/deletePlaylistByID.yaml')
def deletePlaylistByID(targetID):
	"""API Endpoint: Deletes a playlist from the system by providing the playlist id.
	Users can only delete their own playlists while administrators can delete every playlist from the system.

	Args:
		targetID(int): The to be deleted module by id.

	Returns:
		A HTTP-Response code.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401


	targetPlaylist = Playlists.query.filter_by(id = int(targetID)).first()
	if targetPlaylist is None:
		return jsonify(error = 'Playlist does not exist.'), 404

	#check privileges
	if not isAdmin() and targetPlaylist.owner != session['username']:
		return jsonify(error = 'not privileged'), 403

	db_alch.session.delete(targetPlaylist)
	db_alch.session.commit()
	return jsonify(result = 'confirmed')

#tested
@app_rest.route('/_updatePlaylistDescription', methods=['PUT'])
@swag_from('yamldoc/updatePlaylistDescription.yaml')
def updatePlaylistDescription():
	"""API Endpoint: Updates the description text in a playlist.
	Users can only change their own playlists description while the administrator can change every playlist description in the system.

	Returns:
		A HTTP-Response code.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401
	if request.method == 'PUT':
		try:
			data = request.get_json()
			playlistID = data['playlistID']
			comment = data['description']
		except KeyError as e:
			return jsonify(error = 'Invalid Input.'), 400
		#try to obtain desired playlist from db
		playlist = Playlists.query.filter_by(id = playlistID).first()
		if playlist is None:
			return jsonify(error = 'Playlist could not be found.'), 404
		#check privileges
		if not isAdmin() and playlist.owner != session['username']:
			return jsonify(error='not privileged'), 403
		playlist.description = comment
		db_alch.session.commit()
		return jsonify(result = 'confirmed')
	return jsonify('Illegal Method')

#tested
@app_rest.route('/_registerNewPlaylist', methods=['POST'])
@swag_from('yamldoc/registerNewPlaylist.yaml')
def registerNewPlaylist():
	"""API Endpoint: Creates a new playlist for the user by providing a list of module id's.

	Returns:
		A HTTP-Response code.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	if request.method == 'POST':
		data = request.get_json()
		try:
			moduleList = list(set(data['modules']))
			playlistName = data['playlistName']
			user = session['username']
		except KeyError as e:
			return jsonify(error = 'Invalid input'), 400


		#check if there is already a playlist with this name
		possibleExistingPlaylist = Playlists.query.filter(Playlists.owner == user, Playlists.name == playlistName).first()
		if possibleExistingPlaylist is not None:
			return jsonify(error = 'Playlistname already exists.'), 400

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
@swag_from('yamldoc/removeModulesFromPlaylist.yaml')
def removeModulesFromPlaylist():
	"""API Endpoint: Removes Modules from targeted playlist. Users can only modify their own playlists,
	while the administrator can modify all playlists in the system.

	Returns:
		A HTTP-Response codes.

	"""
	if request.method == 'PUT':
		if not 'username' in session:
			return jsonify(error = 'Not logged in.'), 401

		#try to obtain json data from frontend
		try:
			data = request.get_json()
			playlistID = data['playlistID']
			moduleList = data['modules']
		except KeyError as e:
			return jsonify('Invalid Input.'), 400

		#check if you are allowed to modify this playlist
		playlist = Playlists.query.filter_by(id = playlistID).first()
		if playlist is None:
			return jsonify(error = 'Playlist does not exist.'), 404
		if not isAdmin() and playlist.owner != session['username']:
			return jsonify(error = 'not privileged.'), 403

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



#tested
@app_rest.route('/_addModuleToPlaylist/<int:playlistID>/<int:moduleID>', methods=['PUT'])
@swag_from('yamldoc/addModuleToPlaylist.yaml')
def addModuleToPlaylist(playlistID, moduleID):
	"""API Endpoint: Adds a local module to an already existing playlist.
	Users can only modify their own playlists, while the administrator can modify every playlist in the system.

	Args:
		playlistID(int): The id of a playlist on where a new module shall be added.
		moduleID(int): The id of the module which will be added to a playlist.

	Returns:
		A HTTP-Response code.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401
	if request.method == 'PUT':

		#make some checks
		targetPlaylist = Playlists.query.filter_by(id = playlistID).first()
		targetModule = Modules.query.filter_by(id = moduleID).first()
		if targetPlaylist is None or targetModule is None:
			return jsonify(error = 'Playlist or module not found.'), 404
		#check if user is allowed to modify this playlist
		if targetPlaylist.owner != session['username'] and not isAdmin():
			return jsonify(error = 'Not privileged (not your playlist).'), 403

		if targetModule.owner != session['username'] and targetModule.isPrivate == 'false' and not isAdmin():
			return jsonify(error = 'Not privileged (not your module or not public).'), 403

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
@swag_from('yamldoc/addGalaxyRoleToPlaylist.yaml')
def addGalaxyRoleToPlaylist():
	"""API Endpoint: Adds an Ansible Galaxy Role to an existing Playlist. Users can only modify their own playlists,
	while administrators can modify every playlist in the system.

	Returns:
		A HTTP-Response code.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401

	if request.method == 'POST':
		data = request.get_json()
		print(data)
		try:
			playlistID = int(data['playlistID'])
			roleDescription = data['roleDescription']
			roleName = str(data['roleName'])
		except KeyError:
			print("we have key error")
			return jsonify(error = 'invalid input.'), 400

		targetPlaylist = Playlists.query.filter_by(id = playlistID).first()
		if targetPlaylist is None:
			return jsonify(error = 'Playlist not found.'), 404
		#check if user is allowed to modify this playlist
		if targetPlaylist.owner != session['username'] and not isAdmin():
			return jsonify(error = 'Not privileged (not your playlist).'), 403

		#check if module is already in playlist
		playlistModules = targetPlaylist.modules
		for module in playlistModules:
			if str(module.name) == roleName:
				return jsonify(result = "Already in playlist.")

		newGalaxyModule = Modules(roleName, session['username'], roleDescription, 'n/a', 'n/a', 'GALAXY', 'n/a', 'false')
		targetPlaylist.modules.append(newGalaxyModule)
		db_alch.session.commit()
		return jsonify(result = "Galaxy Role has been added to the playlist.")