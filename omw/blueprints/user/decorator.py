from functools import wraps

from flask_login import current_user

from omw.extensions import login_manager


def login_required(role=0, group='open'):
    """
    This is a redefinition of the decorator login_required,
    to include a 'role' argument to allow users with different
    roles access different views and a group access to close some
    views by groups. For example:
    @login_required(role=0, group='ntuwn')   0 = for all
    """

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role < role:
                return login_manager.unauthorized()
            if group != 'open' and current_user.group != group:
                return login_manager.unauthorized()

            return fn(*args, **kwargs)

        return decorated_view

    return wrapper