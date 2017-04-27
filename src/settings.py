# settings.py
import socket
import logging
import os

from dotenv import load_dotenv
from simplepath import SimplePath

path = SimplePath(root='parent')
path.dotenv = path.root / '.env'
OVERRIDE_ENV = ['HTTP_PROXY', 'HTTPS_PROXY']

if path.dotenv.exists():
    if OVERRIDE_ENV:
        for key in OVERRIDE_ENV:
            del os.environ[key]
    load_dotenv(str(path.dotenv))
else:
    logging.warning('Could not find .env file to specify environment variables.')
    logging.warning('Proxy may not be configured properly: file download may not work.')

# log config
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
