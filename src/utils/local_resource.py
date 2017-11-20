import os, platform, subprocess, re, psutil
from src.utils import constants

def get_processor_name():
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
	return str(psutil.cpu_percent())

def get_ram_percent():
	return str(psutil.virtual_memory()[2])

def get_app_version(shell_call):
	try:
		app_version = subprocess.check_output(shell_call, shell=True).strip().decode('utf-8')
		return str(app_version)
	except Exception as e:
		print("App is not installed or not running properly.")
		return "N/A"


