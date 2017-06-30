
from flask import Blueprint, render_template, flash, request, session, jsonify

from src.utils.db_connector import DB_Connector
from src.utils import  local_resource

app = Blueprint('app', __name__)


@app.route('/')
def homepage():
	session['current'] = 'Overview'
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		return render_template("main.html")

@app.route('/login', methods=['POST', 'GET'])
def login_page():
	db = DB_Connector("localhost", "root", "master", "bibicreator")
	try:
		user = request.form['username']
		pw = request.form['password']
		data = db.queryAndResult("SELECT `password` FROM `Users` WHERE `name` = %s", user)[0]
		if data:
			if data[0] == pw:
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

