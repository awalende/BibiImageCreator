"""Container method, which keeps a global db connection with sqlalchemy."""

from flask_sqlalchemy import SQLAlchemy

#container
db = SQLAlchemy()
