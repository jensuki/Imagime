import os
from flask import Flask, session, g, request
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User
from blueprints.users.routes import users_bp
from blueprints.posts.routes import posts_bp
from dotenv import load_dotenv

load_dotenv()

CURR_USER_KEY = 'curr_user'

app = Flask(__name__)

# configurations
app.config['SECRET_KEY'] = 's3cr3tk3y'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///imagime_db')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['DEBUG'] = True

# folder to store user-uploaded images
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'images', 'uploads')

debug = DebugToolbarExtension(app)

# connect DB
connect_db(app)



# register blueprints
app.register_blueprint(users_bp, url_prefix='')
app.register_blueprint(posts_bp, url_prefix='')

@app.before_request
def add_user_to_g():
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None



