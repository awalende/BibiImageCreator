from flask import Flask, render_template, flash, redirect, request, session, abort, url_for
import os
from db_connector import DB_Connector

app = Flask(__name__)



wrong_password = False

@app.route('/')
def homepage():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		return render_template("main.html")
	#return render_template("main.html")

@app.route('/login', methods=['POST', 'GET'])
def login_page():
	db = DB_Connector("localhost", "root", "master", "bibicreator")
	try:
		user = request.form['username']
		pw = request.form['password']
		data = db.queryAndResult("SELECT `Password` FROM `Users` WHERE `Name` = %s", user)
		if data:
			if data[0] == pw:
				print("it worked")
				session['username'] = user
				session['logged_in'] = True
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
    #return redirect(url_for('homepage'))

if __name__ == "__main__":

	app.debug = True
	app.secret_key = os.urandom(5000)
	app.run()
