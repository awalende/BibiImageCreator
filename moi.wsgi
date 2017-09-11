
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/home/awalende/Schreibtisch/FlaskApp/FlaskApp/")

from __init__ import flask_app as application
application.secret_key = 'your secret key. If you share your website, do NOT share it with this key.'
