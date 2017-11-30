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


app_rest = Blueprint('authentication', __name__)


#tested
@app_rest.route('/_generateAuthCookie', methods=['POST'])
@swag_from('yamldoc/getAuthCookie.yaml')
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
		return jsonify(error = 'Invalid username/password'), 401