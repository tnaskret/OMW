from _md5 import md5

from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer

from lib.common_sql import fetch_userid


class User(UserMixin):
    def __init__(self, userID, password, role, group):
        self.id = userID
        self.password = password
        self.role = role
        self.group = group

    def get_auth_token(self):
        """ Encode a secure token for cookie """
        data = [str(self.id), self.password]
        login_serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return login_serializer.dumps(data)

    def get_role(self):
        """ Returns the role (access level) for the user """
        return self.role

    @staticmethod
    def get(userid):
        """
        Static method to search the database and see if userid exists.
        If it does exist then return a User Object. If not then return
        None, as required by Flask-Login.
        """
        user = fetch_userid(userid)

        if user:
            return User(user[0], user[1], user[2], user[3])
        else:
            return None

    @staticmethod
    def hash_pass(password):
        """ Return the md5 hash of the password+salt """
        salted_password = password + current_app.secret_key
        return md5(salted_password.encode('utf-8')).hexdigest()

    def authenticated(self, with_password=True, password=''):
        """
        Ensure a user is authenticated, and optionally check their password.

        :param with_password: Optionally check their password
        :type with_password: bool
        :param password: Optionally verify this as their password
        :type password: str
        :return: bool
        """
        if with_password:
            return self.hash_pass(password) == self.password
        return True

    def is_active(self):
        """
        Return whether or not the user account is active, this satisfies
        Flask-Login by overwriting the default value.

        :return: bool
        """
        return True
