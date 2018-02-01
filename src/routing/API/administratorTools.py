'''This module lists all REST calls for administrator tools.
Documentation for these functions are created by swagger in apidocs/
You should use the interactive swagger documentation, hence it provides more and better documentation.
For the swagger documentation, simply start BibiCreator and point your browser to <URL>/apidocs
'''

from flasgger import swag_from
from flask import Blueprint, jsonify
from src.routing.views import session
from src.utils import local_resource, constants


app_rest = Blueprint('administratorTools', __name__)


def isAdmin():
	if 'username' in session and session['username'] == 'admin':
		return True
	else:
		return False


#tested
@app_rest.route('/_getHealth')
@swag_from('yamldoc/getHealth.yaml')
def getHealth():
	"""API Endpoint: Returns the current cpu and ram usage (only Admin).

	Returns:
		A JSON object containing information about the local machine.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	try:
		if session['username'] == 'admin':
			#build all resource data into a dict
			randomDict = {'cpu_name' : local_resource.get_processor_name(),
						  'cpu_load' : local_resource.get_cpu_load(),
						  'ram_usage': local_resource.get_ram_percent()}
			return jsonify(randomDict)
		else:
			return jsonify(error='not privileged'), 403
	except KeyError:
		return jsonify(error = 'not privileged'), 403


#tested
@app_rest.route('/_getVersions')
@swag_from('yamldoc/getVersions.yaml')
def getVersions():
	"""API Endpoint: Returns the version numbers for automation tools.

	Returns:
		A JSON object describing the versions of the installed automation tools.

	"""
	if not 'username' in session:
		return jsonify(error = 'not logged in'), 401
	dictV = {}
	#ask all external programs for their version numbers.
	dictV['ansible'] = local_resource.get_app_version('ansible --version | head -n 1')
	dictV['packer'] = local_resource.get_app_version(constants.CONFIG.packer_path + ' version')
	dictV['db'] = local_resource.get_app_version('mysql --version')
	return jsonify(dictV)


