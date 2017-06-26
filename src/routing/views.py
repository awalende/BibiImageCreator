
from flask import Blueprint, render_template, flash, request, session

from src.utils.db_connector import DB_Connector

app = Blueprint('app', __name__)


@app.route('/')
def homepage():
	current_page = "Overview"
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
		data = db.queryAndResult("SELECT `Password` FROM `Users` WHERE `Name` = %s", user)
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


@app.route('/logout')
def logout():
	session['logged_in'] = False
	session.pop(session['username'], None)
	return homepage()