"""Module for generating specified packer.json configurations."""

from src.utils import constants


def buildPackerJsonFromConfig(json_data, osImageName):
	"""Assembles a json dict builder for packer.

	Args:
		json_data: Juvenile packer.json content
		osImageName: The name of the new image.

	Returns: An extended json configuration for packer.

	"""
	config = constants.CONFIG

	builder = {
		'type': 'openstack',
		'flavor': config.os_flavor,
		'identity_endpoint': config.os_auth_url,
		'source_image': config.os_base_img_id,
		'image_name': osImageName,
		'username': config.os_user,
		'availability_zone': config.os_availability_zone,
		'password': config.os_password,
		'domain_name': config.os_user_domain_id,
		'ssh_username': config.os_ssh_username,
		'networks': [config.os_network]
	}

	json_data['builders'].append(builder)

	return json_data