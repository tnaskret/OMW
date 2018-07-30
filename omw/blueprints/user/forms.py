from flask_wtf import Form
from wtforms import HiddenField, StringField, PasswordField
from wtforms.validators import DataRequired, Length


class LoginForm(Form):
    next = HiddenField()
    identity = StringField('Username',
                           [DataRequired(), Length(3, 254)])
    password = PasswordField('Password', [DataRequired(), Length(3, 128)])
    # remember = BooleanField('Stay signed in')
