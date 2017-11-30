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


app_rest = Blueprint('administratorTools', __name__)


def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


#tested
@app_rest.route('/_getHealth')
@swag_from('yamldoc/getHealth.yaml')
def getHealth():
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	try:
		if session['username'] == 'admin':
			randomDict = {'cpu_name' : local_resource.get_processor_name(),
						  'cpu_load' : local_resource.get_cpu_load(),
						  'ram_usage': local_resource.get_ram_percent()}
			return jsonify(randomDict)
		else:
			return jsonify(error='not privileged'), 403
	except KeyError:
		return jsonify(error = 'not privileged'), 403


#tested
@app_rest.route('/_getVersions')
@swag_from('yamldoc/getVersions.yaml')
def getVersions():
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	dictV = {}
	dictV['ansible'] = local_resource.get_app_version('ansible --version | head -n 1')
	dictV['packer'] = local_resource.get_app_version(constants.CONFIG.packer_path + ' version')
	dictV['db'] = local_resource.get_app_version('mysql --version')
	return jsonify(dictV)


