
from flask import Blueprint, render_template, flash, request, session, jsonify

from src.utils import  local_resource
from src.sqlalchemy.db_model import *

import src.utils.constants as constants


app = Blueprint('app', __name__)



@app.route('/')
def homepage():
	session['current'] = 'Overview'
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		if session['username'] == 'admin':
			jobs = Jobs.query.all()
			images = constants.OS_CONNECTION.getAllBibiCreatorImages()
		else:
			jobs = Jobs.query.filter_by(owner = session['username'])
			images = constants.OS_CONNECTION.getBibiCreatorImagesByUser(session['username'])



		jinjaData = {'jobs': jobs, 'images': images}
		return render_template("overview.html", data = jinjaData)


@app.route('/history_overview')
def history_overview():
	session['current'] = 'History'
	if not session['logged_in']:
		return homepage()
	return render_template('history_overview.html')


@app.route('/login', methods=['POST', 'GET'])
def login_page():
	try:
		user = request.form['username']
		pw = request.form['password']

		query = Users.query.filter_by(name='admin').first()

		if query:
			if query.password == pw:
				#print("it worked")
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
	if session.get('username') == 'admin':
		session['current'] = 'Resources/Health'
		data = [local_resource.get_processor_name(), local_resource.get_cpu_load(), local_resource.get_ram_percent()]
		return render_template("resources.html", data=data)
	else:
		return homepage()


@app.route('/user_management/')
def userManagement():
	if session.get('username') == 'admin':
		session['current'] = 'User Management'
		return render_template('user_management.html')
	else:
		return homepage()


@app.route('/logout')
def logout():
	session['logged_in'] = False
	session.pop(session['username'], None)
	return homepage()

@app.route('/manage_modules/')
def manageModules():
	session['current'] = 'Manage Modules'

	jinjaData = {}
	#get playlists for jinja templating
	if session.get('username') == 'admin':
		jinjaData['playlists'] = Playlists.query.all()
		jinjaData['ownModules'] = Modules.query.filter_by(owner = 'admin').filter(Modules.module_type != 'GALAXY').all()
		jinjaData['publicModules'] = Modules.query.filter(Modules.owner != 'admin').all()

	else:
		jinjaData['playlists'] = Playlists.query.filter_by(owner = session['username']).all()
		jinjaData['ownModules'] = Modules.query.filter_by(owner = session['username']).all()
		jinjaData['publicModules'] = Modules.query.filter(Modules.owner != session['username'], Modules.isPrivate == 'false').all()

	jinjaData['forcedModules'] = Modules.query.filter_by(isForced = 'true').all()
	return render_template('manage_modules.html', data = jinjaData)


@app.route('/user_settings/')
def user_settings():
	if not 'username' in session:
		return homepage()

	session['current'] = 'Settings'
	return render_template('user_settings.html')

@app.route('/create_image/')
def createImage():
	if session.get('logged_in'):
		session['current'] = 'Create Image'
		return render_template('create_image.html')
	else:
		return homepage()


@app.route('/playlists/<playlistID>/')
def playlistEditor(playlistID):
	session['current'] = 'Manage Playlists'
	if not 'username' in session:
		return homepage()
	id = int(playlistID)
	#try to obtain playlist data from db
	targetPlaylist = Playlists.query.filter_by(id = id).first()
	if targetPlaylist is None:
		return homepage()
	if targetPlaylist.owner != session['username'] or session['username'] != 'admin':
		return homepage()
	return render_template('edit_playlist.html', data = targetPlaylist)




#lets try some jinjaaaaaaaaaaa
#not in rest.py cuz this is pure for filling template data
#todo replace homepage returns to 403 errors
@app.route('/history/<historyid>/')
def showHistoryByID(historyid):
	if not 'username' in session:
		return homepage()
	id = int(historyid)
	#try to obtain history data from db
	targetHistoryRow = History.query.filter_by(id = id).first()
	if targetHistoryRow is None:
		return homepage()
	if targetHistoryRow.owner != session['username'] or session['username'] != 'admin':
		return homepage()
	return render_template('show_history.html', data = targetHistoryRow)

@app.route('/playlists/')
def playlists():
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


	jinjaData = {
		'availableImages': availableImages,
		'currentImage': currentImage
	}
	return render_template('cloud_connection.html', data = jinjaData)




