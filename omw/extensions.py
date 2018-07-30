from flask_login import LoginManager
from flask_wtf import CsrfProtect

login_manager = LoginManager()
csrf = CsrfProtect()
