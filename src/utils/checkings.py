'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
'''

from src.utils import constants, local_resource
import os

#TODO Implement check for new user creation api call
def checkPassedUserFormular(userDict):
	return True

def categorizeAndCheckModule(file):
	"""Checks the incoming installation script file and categorizes it.

	Args:
		file: The incomming file to be categorized.

	Returns:
		A tuple containing the type of the installation script.
	"""
	#get the file extension
	extension = os.path.splitext(file.filename)[1]
	#this is not a valid file!
	if not extension:
		return ('N/A', None)
	#check which files are currently supported by bibicreator
	for tuple in constants.SUPPORTED_EXTENSIONS:
		if tuple[0] == extension:
			return tuple
	return ('N/A', None)

def checkNewModuleForm(formDict):
	"""On new module registration, check all fields if they are valid.

	Args:
		formDict: A JSON-dictionary containing all user input for registration.

	Returns:
		An okay or an detailed error message for the user.

	"""
	if not formDict['moduleName']:
		return "ERROR: Module has no Name!"
	if not formDict['moduleDescriptionText']:
		return "ERROR: Module has no Description!"
	if not formDict['moduleVersion']:
		return "ERROR: Module has no Version!"
	if not (formDict['isPrivate'] == 'true' or formDict['isPrivate'] == 'false'):
		return "ERROR: Could not set privacy to true or false"
	return 'okay'


def checkToolAvailability():
	"""Checks if all automation tools are available.

	Returns:
		True if all tools are there.

	"""
	#check for packer
	if local_resource.get_app_version('ansible --version | head -n 1') == 'N/A':
		print("CRITICAL: Ansible is not installed or not working properly.")
		return False
	if local_resource.get_app_version(constants.CONFIG.packer_path + ' version') == 'N/A':
		print("CRITICAL: Packer is not installed or not working properly.")
		return False
	return True
