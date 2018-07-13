from datetime import timedelta

DEBUG = True
LOG_LEVEL = 'DEBUG'

SERVER_NAME = 'localhost:5000'

REMEMBER_COOKIE_DURATION = timedelta(minutes=30)
SECRET_KEY = '!$flhgSgngNO%$#SOET!$!'

ILI_DTD = 'sql_scripts/WN-LMF.dtd'
UPLOAD_FOLDER = 'public-uploads'
ALLOWED_EXTENSIONS = set(['xml', 'gz', 'xml.gz'])


OMW_DATABASE_FILE_NAME = 'omw.db'
ADMIN_DATABASE_FILE_NAME = 'admin.db'
