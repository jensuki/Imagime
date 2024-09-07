from flask import session, redirect, flash, g

CURR_USER_KEY = 'curr_user'

def do_login(user):
    """Log in user by storing their ID in the session"""

    session[CURR_USER_KEY] = user.id

def do_logout():
    """Log out user"""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

def do_authorize():
    """Authorize user"""

    if not g.user:
        flash('Access unauthorized', 'danger')
        return redirect('/')

