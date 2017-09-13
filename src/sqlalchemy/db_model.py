from src.sqlalchemy.db_alchemy import db



'''
Object representation of underlying MySQL Database
'''



relationship_table = db.Table('jobs_modules',
							  db.Column('id_jobs', db.Integer, db.ForeignKey('jobs.id'), nullable=False),
							  db.Column('id_modules', db.Integer, db.ForeignKey('modules.id'), nullable=False),
							  db.PrimaryKeyConstraint('id_jobs', 'id_modules'))


class Users(db.Model):
	id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
	name = db.Column(db.String(100))
	password = db.Column(db.String(100))
	policy = db.Column(db.String(100))
	max_images = db.Column(db.Integer)
	email = db.Column(db.String(100))


	def __init__(self, name, password, max_images, email, policy='user'):
		self.name = name
		self.password = password
		self.max_images = max_images
		self.email = email
		self.policy = policy

	@property
	def serialize(self):
		return {
			'id'		: self.id,
			'name'		: self.name,
			'password'	: self.password,
			'max_images': self.max_images,
			'email'		: self.email
		}

	def __repr__(self):
		return '<User {}-{}>'.format(self.id, self.name)


class Modules(db.Model):


	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	name = db.Column(db.String(300))
	owner = db.Column(db.String(300))
	description = db.Column(db.Text)
	version = db.Column(db.String(100))
	isPrivate = db.Column(db.String(50))
	module_type = db.Column(db.String(200))
	path = db.Column(db.String(2000))
	isForced = db.Column(db.String(50))
	date = db.Column(db.DateTime)

	@property
	def serialize(self):
	    return {
			'id'			: self.id,
			'name'			: self.name,
			'owner'			: self.owner,
			'description'	: self.description,
			'version'		: self.version,
			'isPrivate'		: self.isPrivate,
			'module_type'	: self.module_type,
			'path'			: self.path,
			'isForced'		: self.isForced,
			'date'			: self.date
		}


	def __repr__(self):
		return '<Module {]-{}>'.format(self.id, self.name)


class Jobs(db.Model):


	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	owner = db.Column(db.String(200))
	name = db.Column(db.String(200))
	status = db.Column(db.String(200))
	progress = db.Column(db.String(200))
	debug_file_path = db.Column(db.String(500))
	base_image_id = db.Column(db.String(200))
	new_image_id = db.Column(db.String(200))
	date = db.Column(db.DateTime)

	modules = db.relationship('Modules', secondary=relationship_table, backref='jobs')

	@property
	def serialize(self):
		return {
			'id'				: self.id,
			'owner'				: self.owner,
			'name'				: self.name,
			'status'			: self.status,
			'progress'			: self.progress,
			'debug_file_path'	: self.debug_file_path,
			'base_image_id'		: self.base_image_id,
			'new_image_id'		: self.new_image_id,
			'date'				: self.date
		}


	def __repr__(self):
		return '<Job {}-{}>'.format(self.id, self.name)