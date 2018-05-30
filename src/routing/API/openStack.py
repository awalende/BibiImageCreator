'''This module lists all REST calls for openStack.
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


app_rest = Blueprint('openStack', __name__)

def isAdmin():
	"""Checks if the currently logged in user is the administrator.

	Returns:
		True if admin.

	"""
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False



#only tested in backend
#used in history_overview.html
@app_rest.route('/_getOsIDFromOSName/<os_image_name>', methods=['GET'])
@swag_from('yamldoc/getOsIDFromOSName.yaml')
def getOSIDFromOSName(os_image_name):
	"""API Endpoint: Returns the OpenStack-ImageID from a provided OpenStack-Imagename.

	Args:
		os_image_name(str): The openstack image name for the lookup.

	Returns:
		A JSON object containing the id of the OpenStack-Image.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401

	if request.method == 'GET':
		if not os_image_name:
			return jsonify(error = 'Invalid Input'), 400
		os_image_id = constants.OS_CONNECTION.findImageIdByName(os_image_name)
		return jsonify(result = os_image_id)
	return jsonify(error = 'not allowed'), 403


#tested
@app_rest.route('/_getOSImages')
@swag_from('yamldoc/getOSImages.yaml')
def getOSImages():
	"""API Endpoint: Returns all images from Openstack created by BibiCreator.
	Users will only retreive their own created images,
	while administrators will retreive all images created by BibiCreator.

	Returns:
		A JSON object containing a list of all OPenStack images.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in.'), 401
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
@app_rest.route('/_deleteOSImageByName/<imageName>', methods=['DELETE'])
@swag_from('yamldoc/deleteOSImageByName.yaml')
def deleteOSImageByName(imageName):
	"""API Endpoint: Deletes a specified BibiCreator Image from OpenStack.
	Only images created by BibiCreator can be deleted.
	Users can only delete their own BibiCreator images,
	while administrator can delete every BibiCreator Image from OpenStack.

	Args:
		imageName(str): The image to be deleted by name.

	Returns:
		A HTTP status code.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in.'), 401

	if request.method == 'DELETE':
		if imageName is None:
			return jsonify(error = 'Invalid Input.'), 400
		if isAdmin():
			images = constants.OS_CONNECTION.getAllBibiCreatorImages()
		else:
			images = constants.OS_CONNECTION.getBibiCreatorImagesByUser(session['username'])
		for image in images:
			if image.name == imageName:
				constants.OS_CONNECTION.deleteImageByName(image.name)
				return jsonify(result = 'confirmed')
		return jsonify(error = 'could not find image with such name.'), 404
	return jsonify(error = 'Invalid Method.')

#tested
@app_rest.route('/_changeBaseImgByID/<imgID>', methods=['PUT'])
@swag_from('yamldoc/changeBaseImgByID.yaml')
def changeBaseImgByID(imgID):
	"""API Endpoint: Changes the base image for new BibiCreator builds by providing an OpenStack-ImageID.
	This does not check if the image id is valid or existing in OpenStack.

	Args:
		imgID(int): The image by id to be set as new base image.

	Returns:
		A HTTP status code.

	"""
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401

	if not isAdmin():
		return jsonify(error = 'Not privileged.'), 403

	if request.method == 'PUT':
		constants.CONFIG.os_base_img_id = imgID
		return jsonify(result = 'confirmed')

@app_rest.route('/_ostest')
def ostests():
	rndmList = []
	for image in constants.OS_CONNECTION.conn.image.images():
		rndmList.append(image.name)
	return jsonify(rndmList)
