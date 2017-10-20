
from openstack import connection
from openstack.exceptions import HttpException


class OpenStackConnector:

	def __init__(self, user, password, project_name, auth_url, version='2'):
		try:
			self.conn = connection.Connection(auth_url=auth_url, username=user, password=password, project_name=project_name, user_domain_id='default', project_domain_name='default')
		except HttpException as e:
			print('Could not authorize to openstack. Credentials wrong or server down.')


	def getBibiCreatorImagesByUser(self, bibicreator_user):
		#get all images from openstack and filter them
		userImages = []
		for image in self.conn.image.images():
			nameParts = image.name.split('-')
			if nameParts.__len__() != 4:
				continue
			if nameParts[0] != 'bibicreator':
				continue
			if nameParts[1] == bibicreator_user:
				userImages.append(image)
		return userImages


	def getAllBibiCreatorImages(self):
		allImages = []
		for image in self.conn.image.images():
			nameParts = image.name.split('-')
			if nameParts.__len__() != 4:
				continue
			if nameParts[0] != 'bibicreator':
				continue
			allImages.append(image)
		return allImages

	def deleteImageByName(self, imageName):
		targetImage = self.conn.image.find_image(imageName, ignore_missing=True)
		if targetImage is None:
			return
		#kill it with fire
		self.conn.image.delete_image(targetImage, ignore_missing=True)


