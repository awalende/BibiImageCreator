'''
	BibiCreator v0.1 (24.01.2018)
	Alex Walender <awalende@cebitec.uni-bielefeld.de>
	CeBiTec Bielefeld
	Ag Computational Metagenomics
'''

import os, platform, subprocess, re, psutil
from src.utils import constants

def get_processor_name():
	"""Obtains the processor information of this local machine.

	Returns:
		The name and capabilites of the cpu.

	"""
	if platform.system() == "Windows":
		return platform.processor()
	elif platform.system() == "Darwin":
		os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
		command ="sysctl -n machdep.cpu.brand_string"
		return subprocess.check_output(command).strip()
	elif platform.system() == "Linux":
		command = "cat /proc/cpuinfo"
		all_info = subprocess.check_output(command, shell=True).strip().decode("utf-8")
		for line in all_info.split("\n"):
			if "model name" in line:
				return re.sub( ".*model name.*:", "", line,1)
	return ""

def get_cpu_load():
	"""Obtains current cpu load.

	Returns:
		CPU load percentage.

	"""
	return str(psutil.cpu_percent())

def get_ram_percent():
	"""Obtains current RAM load.

	Returns:
		The current load of RAM.

	"""
	return str(psutil.virtual_memory()[2])

def get_app_version(shell_call):
	"""Executes a shell call for obtaining version numbers of an app.

	Args:
		shell_call: A unix shell call which returns a version.

	Returns:
		The app version number.

	"""
	try:
		app_version = subprocess.check_output(shell_call, shell=True).strip().decode('utf-8')
		return str(app_version)
	except Exception as e:
		print("App is not installed or not running properly.")
		return "N/A"


