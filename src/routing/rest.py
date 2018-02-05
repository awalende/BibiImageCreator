"""This module is for debugging reasons and will be deleted soon."""
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



app_rest = Blueprint('app_rest', __name__)

DB_CREDENTIALS = ('localhost', 'root', 'master', 'bibicreator')



def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


###########ALCHEMY TESTS########################

@app_rest.route('/_test')
def testroute():
	"""debugging stuff"""
	return jsonify()


