
"""This module lists all available flask routings for the user interface.
These decorated functions deliver the user a rendered webpage with the help of
html templates und the jinja2 templating engine."""
from flask import Blueprint, render_template, flash, request, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from src.utils import  local_resource
from src.sqlalchemy.db_model import *

import src.utils.constants as constants


#register this file as a blueprint
app = Blueprint('app', __name__)


@app.route('/')
def homepage():
	"""Either routes the user to the login page or to the default overview page."""
	session['current'] = 'Overview'
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		return render_template("overview.html")


@app.route('/history_overview')
def history_overview():
	"""Routes the user to the history overview page."""
	session['current'] = 'History'
	if not session['logged_in']:
		return homepage()

	#gethistory list from database
	if session['username'] == 'admin':
		historyList = History.query.all()
	else:
		historyList = History.query.filter_by(owner = session['username']).all()

	#we dont want to see historys who are not finished building yet.
	for history in historyList:
		if history.isReady == 'false':
			historyList.remove(history)

	return render_template('history_overview.html', data = list(reversed(historyList)))


@app.route('/login', methods=['POST', 'GET'])
def login_page():
	"""Standard default log in page for authentication."""
	try:
		user = request.form['username']
		pw = request.form['password']
		query = Users.query.filter_by(name= user).first()
		if query:
			#if the user authentication is succesful, create a new session
			if check_password_hash(query.password, pw):
				session['username'] = user
				session['logged_in'] = True
				session['current'] = "Overview"
			else:
				flash("You have entered wrong credentials.")
	except Exception as e:
		print(e)
		flash("You have entered wrong credentials.")
	return homepage()

@app.route('/resources/')
def resourceAndHealth():
	"""Admin only page for checking the cpu and package health of the local machine."""
	if session.get('username') == 'admin':
		session['current'] = 'Resources/Health'
		#obtain all resource data from this local machine
		data = [local_resource.get_processor_name(), local_resource.get_cpu_load(), local_resource.get_ram_percent()]
		return render_template("resources.html", data=data)
	else:
		return homepage()


@app.route('/user_management/')
def userManagement():
	"""Admin only page for managing all users in bibicreator."""
	if session.get('username') == 'admin':
		session['current'] = 'User Management'
		return render_template('user_management.html')
	else:
		return homepage()


@app.route('/logout')
def logout():
	"""Pops the session of the currently logged in user."""
	session['logged_in'] = False
	session.pop(session['username'], None)
	return homepage()

@app.route('/manage_modules/')
def manageModules():
	"""Routes to the module manager. First it gathers all available modules for this user."""
	session['current'] = 'Manage Modules'

	jinjaData = {}
	#get playlists for jinja templating, admin gets all playlists
	if session.get('username') == 'admin':
		jinjaData['playlists'] = Playlists.query.all()
		jinjaData['ownModules'] = Modules.query.filter_by(owner = 'admin').filter(Modules.module_type != 'GALAXY').all()
		jinjaData['publicModules'] = Modules.query.filter(Modules.owner != 'admin').all()
	#while regular users dont...
	else:
		jinjaData['playlists'] = Playlists.query.filter_by(owner = session['username']).all()
		jinjaData['ownModules'] = Modules.query.filter_by(owner = session['username']).all()
		jinjaData['publicModules'] = Modules.query.filter(Modules.owner != session['username'], Modules.isPrivate == 'false').all()

	jinjaData['forcedModules'] = Modules.query.filter_by(isForced = 'true').all()
	return render_template('manage_modules.html', data = jinjaData)


@app.route('/user_settings/')
def user_settings():
	"""Routes the user to page, where they can change their passwords."""
	if not 'username' in session:
		return homepage()
	session['current'] = 'Settings'
	return render_template('user_settings.html')

@app.route('/create_image/')
def createImage():
	"""Routes the user to the assisted image creation page."""
	if session.get('logged_in'):
		session['current'] = 'Create Image'
		return render_template('create_image.html')
	else:
		return homepage()


@app.route('/playlists/<playlistID>/')
def playlistEditor(playlistID):
	"""Lets users edit their playlists. First obtain playlist data from db.

	Args:
		playlistID: The targeted playlist.

	"""
	session['current'] = 'Manage Playlists'
	if not 'username' in session:
		return homepage()
	id = int(playlistID)
	#try to obtain playlist data from db
	targetPlaylist = Playlists.query.filter_by(id = id).first()
	#if there is no playlist, or the user is not allowed to, reroute them back.
	if targetPlaylist is None:
		return homepage()
	if targetPlaylist.owner != session['username'] and session['username'] != 'admin':
		return homepage()
	return render_template('edit_playlist.html', data = targetPlaylist)



#todo replace homepage returns to 403 errors
@app.route('/history/<historyid>/')
def showHistoryByID(historyid):
	"""Let the user inspect the history by a specific id.

	Args:
		historyid: The desired history id.

	"""
	if not 'username' in session:
		return homepage()
	id = int(historyid)
	#try to obtain history data from db
	targetHistoryRow = History.query.filter_by(id = id).first()
	if targetHistoryRow is None:
		return homepage()
	if targetHistoryRow.owner != session['username'] and session['username'] != 'admin':
		return homepage()
	return render_template('show_history.html', data = targetHistoryRow)

@app.route('/playlists/')
def playlists():
	"""Renders the playlist overview page."""
	session['current'] = 'Manage Playlists'
	if not 'username' in session:
		return homepage()
	#obtain playlists from the logged in users
	playlists = Playlists.query.filter_by(owner = session['username']).all()
	if session['username'] == 'admin':
		playlists = Playlists.query.all()
	return render_template('show_playlists.html', data = playlists)


@app.route('/cloud_connection/')
def cloud_connection():
	"""Admin only page for setting a new base image."""
	osConn = constants.OS_CONNECTION
	conf = constants.CONFIG
	session['current'] = 'Cloud Connection'
	if not 'username' in session:
		return homepage()
	if not session['username'] == 'admin':
		return homepage()

	availableImages = []
	for image in osConn.getAllImages():
		tmpDict = {'name': image.name,
				   'id': image.id,
				   'size': int(image.size / 1000000),
				   'status': image.status
				   }
		availableImages.append(tmpDict)

	#obtain the current base img
	currentBaseImage = osConn.getImageByID(conf.os_base_img_id)
	if currentBaseImage is not None:
		currentImage = {
			'name': currentBaseImage.name,
			'id': currentBaseImage.id
		}
	else:
		currentImage = {
			'name': 'N/A',
			'id': 'N/A'
		}

	#build new jinja template data for available images and the current image
	jinjaData = {
		'availableImages': availableImages,
		'currentImage': currentImage
	}
	return render_template('cloud_connection.html', data = jinjaData)




