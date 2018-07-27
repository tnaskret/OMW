from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    url_for,
    render_template)
from flask_login import (
    login_user,
    current_user,
    logout_user)

from lib.safe_next_url import safe_next_url
from omw.blueprints.user.decorator import login_required
from omw.blueprints.user.models import User

user = Blueprint('user', __name__, template_folder='templates')


@user.route("/login", methods=["GET", "POST"])
def login():
    """ This login function checks if the username & password
    match the admin.db; if the authentication is successful,
    it passes the id of the user into login_user() """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == "POST" and \
            "username" in request.form and \
            "password" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        user = User.get(username)

        # If we found a user based on username then compare that the submitted
        # password matches the password in the database. The password is stored
        # is a slated hash format, so you must hash the password before comparing it.
        if user and user.hash_pass(password) == user.password:

            if login_user(user, remember=True) and user.is_active:
                next_url = request.form.get('next')
                if next_url:
                    return redirect(safe_next_url(next_url))
                return redirect(url_for("index"))
            else:
                flash('This account has been disabled.', 'error')
        else:
            flash('Identity or password is incorrect.', 'error')
    return render_template("user/login.html")


@user.route("/logout")
@login_required(role=0, group='open')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))

