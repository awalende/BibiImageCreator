from flask import Flask, render_template, flash, redirect, request, session, abort, url_for
import os

app = Flask(__name__)

@app.route('/')
def homepage():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		return render_template("main.html")
	#return render_template("main.html")

@app.route('/login', methods=['POST', 'GET'])
def login_page():
	if request.form['password'] == 'password' and request.form['username'] == 'admin':
		session['username'] = 'admin'
		session['logged_in'] = True
	else:
		flash('wrong password')
	return homepage()


@app.route('/logout')
def logout():
    session['logged_in'] = False
    session.pop(session['username'], None)
    return redirect(url_for('homepage'))

if __name__ == "__main__":
	app.debug = True
	app.secret_key = os.urandom(5000)
	app.run()
