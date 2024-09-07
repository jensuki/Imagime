from flask import Blueprint, render_template, redirect, flash, session, g, url_for
from models import db, User, Post, FavoritedSong, PostSong
from forms import SignUpForm, LoginForm, EditProfileForm, AddImageForm
from utils.helpers import do_login, do_logout, do_authorize


CURR_USER_KEY = 'curr_user'

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/')
def home():
    """
    Display home page if user is loggged in
    Display home-anon if anon user

    """

    if g.user:
        # retrieve 20 most recent posts
        posts = (Post
                 .query
                 .order_by(Post.timestamp.desc())
                 .limit(10)
                 .all())

        return render_template('home.html', posts=posts)

    else:
        return render_template('home-anon.html')

