'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
'''
from openstack import connection
from openstack.exceptions import HttpException


class OpenStackConnector:
	"""Connects to OpenStack via sdk."""

	def __init__(self, user, password, project_name, auth_url, user_domain_id, project_domain_name, version='2'):
		"""Initializes an OpenStack Connection

		Creates a new connection to OpenStack with some provided credentials by using the
		OpenStack SDK.

		Args:
		    user: OpenStack Username
		    password: The password of the openstack username.
		    project_name: The name of the openstack project which will be connected to.
		    auth_url: The endpoint for authorization in openstack.
		    user_domain_id: The id of the targetede user domain.
		    project_domain_name: The targeted name of the project domain.
		    version: Targeted endpoint version.

		Raises:
		    HttpException: If the openstack went down or the credentials were wrong.
		"""
		try:
			self.conn = connection.Connection(auth_url=auth_url, username=user, password=password, project_name=project_name, user_domain_id=user_domain_id, project_domain_name=project_domain_name)
		except HttpException as e:
			print('Could not authorize to openstack. Credentials wrong or server down.')


	def getBibiCreatorImagesByUser(self, bibicreator_user):
		"""Returns all BibiCreator Images from Neutron by a given user.

		Returns all BibiCreator Images from OpenStack, which have been
		created by BibiCreator.

		Args:
		    bibicreator_user: The BibiCreator-Username for the targeted images on Neutron.

		Returns:
		    A list containing all images from OpenStack, which are owned by the given user.
		"""
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
		"""Returns all BibiCreator Images.

		Returns all BibiCreator Images from OpenStack-Neutron.

		Returns:
		    A list containing all BibiCreator-Images from OpenStack.
		"""
		allImages = []
		for image in self.conn.image.images():
			nameParts = image.name.split('-')
			if nameParts.__len__() != 4:
				continue
			if nameParts[0] != 'bibicreator':
				continue
			allImages.append(image)
		return allImages

	def getAllImages(self):
		"""Returns all OpenStack-Images.

		Returns:
		    All OpenStack-Images from the Neutron Service.

		"""
		allImages = self.conn.image.images()
		return allImages


	def findImageIdByName(self, imageName):
		"""Finds and returns an OpenStack ImageID by name.

		Args:
		    imageName: The desired image by name.

		Returns:
		    An id from an image from OpenStack.
		"""
		targetImage = self.conn.image.find_image(imageName, ignore_missing=True)
		if targetImage is None:
			return
		return targetImage.id


	def deleteImageByName(self, imageName):
		"""Deletes an image from OpenStack

		Args:
		    imageName: The desired image by name.

		"""
		targetImage = self.conn.image.find_image(imageName, ignore_missing=True)
		if targetImage is None:
			return
		#kill it with fire
		self.conn.image.delete_image(targetImage, ignore_missing=True)


	#may return none
	def getImageByID(self, image_id):
		"""Returns an image from OpenStack by id.

		Args:
		    image_id: The desired image by id.

		Returns:
		    The targeted image from OpenStack.

		"""
		targetImage = self.conn.image.find_image(image_id, ignore_missing=True)
		return targetImage



	#make some random query and if this does not work, we then don't have a valid connection.
	def isValidConnection(self):
		"""Checks if the connection to OpenStack is valid.

		Returns: True of False.

		"""
		try:
			testList = self.conn.image.images()
		except Exception as e:
			return False
		return True




