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


app_rest = Blueprint('history', __name__)

def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


#tested
@app_rest.route('/_getHistory', methods = ['GET'])
@swag_from('yamldoc/getHistory.yaml')
def getHistory():
	if not 'username' in session:
		return jsonify(error = 'Not logged in.'), 401
	#if admin, return every history made
	if session['username'] == 'admin':
		query = History.query.all()
		historyList = [i.serialize for i in query]
	else:
		query = History.query.filter_by(owner = session['username']).all()
		historyList = [i.serialize for i in query]
	return jsonify(historyList)