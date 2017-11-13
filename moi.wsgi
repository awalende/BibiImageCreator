
import sys
import logging
import os
logging.basicConfig(stream=sys.stderr)

os.environ['http_proxy'] = 'http://proxy.cebitec.uni-bielefeld.de:3128'
os.environ['HTTP_PROXY'] = 'http://proxy.cebitec.uni-bielefeld.de:3128'

os.environ['https_proxy'] = 'https://proxy.cebitec.uni-bielefeld.de:3128'
os.environ['HTTPS_PROXY'] = 'https://proxy.cebitec.uni-bielefeld.de:3128'

os.environ['no_proxy'] = 'localhost,127.0.0.1,169.254.169.254,swift,openstack.cebitec.uni-bielefeld.de'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,169.254.169.254,swift,openstack.cebitec.uni-bielefeld.de'

os.environ['PATH'] = '/home/ubuntu/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin'


sys.path.insert(0,"/home/awalende/Schreibtisch/FlaskApp/FlaskApp/")

from __init__ import flask_app as application
application.secret_key = 'your secret key. If you share your website, do NOT share it with this key.'
