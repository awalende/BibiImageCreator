from src.sqlalchemy.db_alchemy import db



'''
Object representation of underlying MySQL Database
'''

class Users(db.Model):
	id = db.Column(db.Integer, primary_key=True, unique=True)
	name = db.Column(db.String(100))
	password = db.Column(db.String(100))
	policy = db.Column(db.String(100))
	max_images = db.Column(db.Integer)
	email = db.Column(db.String(100))

	@property
	def serialize(self):
		return {
			'id'		: self.id,
			'name'		: self.name,
			'password'	: self.password,
			'max_images': self.max_images,
			'email'		: self.email
		}