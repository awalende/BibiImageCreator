from src.utils import constants
import os

#TODO Implement check for new user creation api call
def checkPassedUserFormular(userDict):
	return True

def categorizeAndCheckModule(file):
	extension = os.path.splitext(file.filename)[1]
	#print("Got as extension: " + str(extension))
	if not extension:
		return ('N/A', None)
	for tuple in constants.SUPPORTED_EXTENSIONS:
		if tuple[0] == extension:
			return tuple
	return ('N/A', None)

def checkNewModuleForm(formDict):
	if not formDict['moduleName']:
		return "ERROR: Module has no Name!"
	if not formDict['moduleDescriptionText']:
		return "ERROR: Module has no Description!"
	if not formDict['moduleVersion']:
		return "ERROR: Module has no Version!"
	if not (formDict['isPrivate'] == 'true' or formDict['isPrivate'] == 'false'):
		return "ERROR: Could not set privacy to true or false"
	return 'okay'

