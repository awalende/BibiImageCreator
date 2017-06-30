from flask import Blueprint, render_template, flash, request, session, jsonify
from src.utils import  local_resource
from src.utils.db_connector import DB_Connector

app_rest = Blueprint('app_rest', __name__)

#TODO: Unify db calls

#TODO: Make only accessible from admin
@app_rest.route('/_getHealth')
def getHealth():
	randomDict = {'cpu_name' : local_resource.get_processor_name(),
				  'cpu_load' : local_resource.get_cpu_load(),
				  'ram_usage': local_resource.get_ram_percent()}
	return jsonify(randomDict)

@app_rest.route('/_getVersions')
def getVersions():
	dictV = {}
	dictV['ansible'] = local_resource.get_app_version('ansible --version | head -n 1')
	dictV['packer'] = local_resource.get_app_version('./packer version')
	try:
		db = DB_Connector('localhost', 'root', 'master', 'bibicreator')
		dictV['db'] = db.queryAndResult('SELECT VERSION()', None)[0]
	except Exception as e:
		print(e)
		dictV['db'] = 'N/A'
	return jsonify(dictV)

@app_rest.route('/_getUsers')
def getUsers():
	main_dictV = {}
	try:
		db = DB_Connector('localhost', 'root', 'master', 'bibicreator')
	except Exception as e:
		print(e)
		return jsonify('N/A')
	result = db.queryAndResult('SELECT id, name, policy, max_images FROM Users', None)
	#print(result)
	return jsonify(result)
