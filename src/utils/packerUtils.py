from src.utils import constants


def buildPackerJsonFromConfig(json_data, osImageName):
	config = constants.CONFIG

	builder = {
		'type': 'openstack',
		'flavor': config.os_flavor,
		'identity_endpoint': config.os_auth_url,
		'source_image': config.os_base_img_id,
		'image_name': osImageName,
		'username': config.os_user,
		'password': config.os_password,
		'domain_name': config.os_user_domain_id,
		'ssh_username': config.os_ssh_username,
		'networks': [config.os_network]
	}

	json_data['builders'].append(builder)

	return json_data