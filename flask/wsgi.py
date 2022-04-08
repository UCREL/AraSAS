import sys, time, os
if os.path.isdir("/var/www/arabic-usas-python"):
	activate_this = '/var/www/arabic-usas-python/flask/uvenv/bin/activate_this.py'
	with open(activate_this) as file_:
	    exec(file_.read(), dict(__file__=activate_this))

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

sys.path.insert(0, "/var/www/arabic-usas-python/flask")

from app import app as application
