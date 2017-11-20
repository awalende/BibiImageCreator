from src.sqlalchemy.db_alchemy import db
from datetime import datetime



'''
Object representation of underlying MySQL Database
'''


jobsXmodules = db.Table('jobs_modules',
						db.Column('id_jobs', db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
						db.Column('id_modules', db.Integer, db.ForeignKey('modules.id' , ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
						db.PrimaryKeyConstraint('id_jobs', 'id_modules'))


historyXhistoryModules = db.Table('history_historyModules',
								  db.Column('id_history', db.Integer, db.ForeignKey('history.id'), nullable=False),
								  db.Column('id_historyModule', db.Integer, db.ForeignKey('historyModules.id'), nullable=False),
								  db.PrimaryKeyConstraint('id_history', 'id_historyModule'))

playlistXmodules = db.Table('playlist_modules',
							db.Column('id_playlist', db.Integer, db.ForeignKey('playlists.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
							db.Column('id_modules', db.Integer, db.ForeignKey('modules.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
							db.PrimaryKeyConstraint('id_playlist', 'id_modules')
							)


class Playlists(db.Model):
	id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
	name = db.Column(db.String(100))
	owner = db.Column(db.String(1000))
	description = db.Column(db.String(10000))
	date = db.Column(db.DateTime, default=db.func.current_timestamp())

	modules = db.relationship('Modules', secondary=playlistXmodules, backref='playlists')

	def __init__(self, name, owner, description):
		self.name = name
		self.owner = owner
		self.description = description

	@property
	def serialize(self):
		return {
			'id'			: self.id,
			'name'			: self.name,
			'owner'			: self.owner,
			'description'	: self.description,
			'date'			: self.date
		}

	def __repr__(self):
		return '<Playlist {}-{}>'.format(self.id, self.name)



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



class History(db.Model):

	__tablename__ = 'history'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	owner = db.Column(db.String(200))
	name = db.Column(db.String(200))
	commentary = db.Column(db.Text)

	debug_file_path = db.Column(db.String(500))
	base_image_id = db.Column(db.String(200))
	new_image_id = db.Column(db.String(200))
	isReady = db.Column(db.String(50))
	date = db.Column(db.DateTime, default=db.func.current_timestamp())

	modules = db.relationship('HistoryModules', secondary=historyXhistoryModules, backref='history')


	def __init__(self, owner, name, commentary, debug_file_path, base_image_id, isReady, new_image_id):
		self.owner = owner
		self.name = name
		self.commentary = commentary
		self.debug_file_path = debug_file_path
		self.base_image_id = base_image_id
		self.isReady = isReady
		self.new_image_id = new_image_id


	def __repr__(self):
		return '<History {}-{}>'.format(self.id, self.name)

	@property
	def serialize(self):
		return {
			'id'				: self.id,
			'name'				: self.name,
			'owner'				: self.owner,
			'commentary' 		: self.commentary,
			'debug_file_path'	: self.debug_file_path,
			'base_image_id'		: self.base_image_id,
			'new_image_id'		: self.new_image_id,
			'isReady'			: self.isReady,
			'date'				: self.date,
			'modules'			: [i.serialize for i in self.modules]
		}





class HistoryModules(db.Model):

	__tablename__ = 'historyModules'

	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	name = db.Column(db.String(300))
	owner = db.Column(db.String(300))
	description = db.Column(db.Text)
	version = db.Column(db.String(100))
	module_type = db.Column(db.String(200))
	path = db.Column(db.String(2000))
	isForced = db.Column(db.String(50))
	date = db.Column(db.DateTime, default=db.func.current_timestamp())

	def __init__(self, name, owner, description, version, module_type, path, isForced):
		self.name = name
		self.owner = owner
		self.description = description
		self.version = version
		self.module_type = module_type
		self.path = path
		self.isForced = isForced


	@property
	def serialize(self):
		return {
			'id'			: self.id,
			'name'			: self.name,
			'owner'			: self.owner,
			'description'	: self.description,
			'version'		: self.version,
			'module_type'	: self.module_type,
			'path'			: self.path,
			'isForced'		: self.isForced,
			'date'			: self.date
		}

	def __repr__(self):
		return '<HistoryModule {}-{}>'.format(self.id, self.name)






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
	date = db.Column(db.DateTime, default=db.func.current_timestamp())

	def __init__(self, name, owner, description, version, isPrivate, module_type, path, isForced):
		self.name = name
		self.owner = owner
		self.description = description
		self.version = version
		self.isPrivate = isPrivate,
		self.module_type = module_type
		self.path = path
		self.isForced = isForced




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
		return '<Module {}-{}>'.format(self.id, self.name)


class Jobs(db.Model):


	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	owner = db.Column(db.String(200))
	name = db.Column(db.String(200))
	status = db.Column(db.String(200))


	progression = db.Column(db.Text, default='n/a')

	debug_file_path = db.Column(db.String(500))
	base_image_id = db.Column(db.String(200))
	new_image_id = db.Column(db.String(200))
	date = db.Column(db.DateTime, default=db.func.current_timestamp())

	modules = db.relationship('Modules', secondary=jobsXmodules, backref='jobs')



	def __init__(self, name, owner, status,  debug_file_path, base_image_id, new_image_id):
		self.name = name
		self.owner = owner
		self.status = status

		self.debug_file_path = debug_file_path
		self.base_image_id = base_image_id
		self.new_image_id = new_image_id


	@property
	def serialize(self):
		return {
			'id'				: self.id,
			'owner'				: self.owner,
			'name'				: self.name,
			'status'			: self.status,
			'progression'		: self.progression,
			'debug_file_path'	: self.debug_file_path,
			'base_image_id'		: self.base_image_id,
			'new_image_id'		: self.new_image_id,
			'date'				: self.date
		}


	def __repr__(self):
		return '<Job {}-{}>'.format(self.id, self.name)