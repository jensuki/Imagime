import os
from flask import Flask, session, g
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User
from blueprints.users.routes import users_bp
from blueprints.posts.routes import posts_bp

CURR_USER_KEY = 'curr_user'

app = Flask(__name__)

# configurations
app.config['SECRET_KEY'] = 's3cr3tk3y'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///imagime_db')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# folder to store user-uploaded images
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'images', 'uploads')

debug = DebugToolbarExtension(app)

connect_db(app)

# register blueprints
app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(posts_bp, url_prefix='/posts')

@app.before_request
def add_user_to_g():
    """Add currently logged in user to global 'g' object"""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None