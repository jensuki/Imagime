import os
from flask import Blueprint, render_template, redirect, request, flash, session, g, url_for, current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from models import db, User, Post, FavoritedSong
from forms import SignUpForm, LoginForm, EditProfileForm
from utils.helpers import do_login, do_logout, do_authorize

CURR_USER_KEY = 'curr_user'

users_bp = Blueprint('users', __name__)

@users_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Show signup form + handle form submission"""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

    form = SignUpForm()

    if form.validate_on_submit():
        print('Form validated successfully')
        try:
            # handle profile image
            profile_img_url = form.profile_img_url.data
            profile_img_file = form.profile_img_file.data
            profile_img = None

            # check if image file has been uploaded
            if profile_img_file:
                filename = secure_filename(profile_img_file.filename)
                profile_img_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                profile_img_file.save(profile_img_path)
                profile_img = url_for('static', filename=f'images/uploads/{filename}') # store image path in DB
            elif profile_img_url:
                profile_img = profile_img_url # store image URL directly in DB
            else:
                profile_img = url_for('static', filename=f'images/assets/default-pic.png') # default if neither

            # add user to DB
            new_user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                profile_img=profile_img
            )

            db.session.commit()

            do_login(new_user)
            flash(f'Welcome {new_user.username}!', 'success')
            return redirect(url_for('posts.home'))

        except IntegrityError:
            db.session.rollback()
            flash('Username or email already taken', 'danger')

    # else:
    #     print('Form did not validate')
    #     for field, errors in form.errors.items():
    #         for error in errors:
    #             print(f'Error in {field}: {error}')

    return render_template('users/signup.html', form=form)

@users_bp.route('/login', methods=['GET','POST'])
def login():
    """Show login form + handle form submission"""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data
        )

        if user:
            do_login(user)
            flash(f'Welcome back, {user.username}', 'success')
            return redirect(url_for('posts.home'))

        flash('Invalid credentials', 'danger')

    return render_template('users/login.html', form=form)

@users_bp.route('/logout')
def logout():
    """Handle user logging out"""

    do_logout()

    flash('You have successfully logged out', 'success')
    return redirect(url_for('users.login'))

@users_bp.route('/users')
def list_users():
    """Page displaying a list of all users"""

    search = request.args.get('q','')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.ilike(f'%{search}%')).all()

    return render_template('users/index.html', users=users)

@users_bp.route('/users/<int:user_id>', methods=['GET'])
def user_profile(user_id):
    """Display users profile with their posts if any"""

    if not g.user:
        flash('You must be logged in to view this page', 'danger')
        return redirect(url_for('users.login'))

    user = User.query.get_or_404(user_id)

    # if posts, display users posts by newest first (user.posts)
    posts = (Post
             .query
             .filter(Post.user_id == user_id)
             .order_by(Post.timestamp.desc())
             .limit(3)
             .all())

    return render_template('users/profile.html', user=user, posts=posts)

@users_bp.route('/users/profile', methods=['GET', 'POST'])
def edit_profile():
    """Update logged-in users profile"""

    do_authorize()

    form = EditProfileForm(obj=g.user)

    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data):
            g.user.username = form.username.data
            g.user.email = form.email.data

            # handle image file upload first
            if form.profile_img_file.data:
                # process the uploaded file
                file = form.profile_img_file.data
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/images/uploads', filename)
                file.save(file_path)
                g.user.profile_img = f'/static/images/uploads/{filename}'

            # then handle URL if no file uploaded
            elif form.profile_img_url.data:
                g.user.profile_img = form.profile_img_url.data

            # if URL field is '', set default image, unlesss theres an uploaded image
            elif form.profile_img_url.data == '':
                if not g.user.profile_img.startswith('/static/images/uploads/'):
                    g.user.profile_img = url_for('static', filename='images/assets/default-pic.png')

            # handle optional bio field
            g.user.bio = form.bio.data or ''

            db.session.commit()
            flash('Profile successfully updated', 'success')
            return redirect(url_for('users.user_profile', user_id=g.user.id))

        flash('Incorrect password, please try again', 'danger')

    return render_template('/users/edit.html', form=form, user_id=g.user.id)

@users_bp.route('/users/delete', methods=['POST'])
def delete_user():
    """Delete a users account from DB"""

    do_authorize()

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect(url_for('users.signup'))

@users_bp.route('/users/<int:user_id>/favorited')
def show_favorited_songs(user_id):
    """Display a logged in users favorited songs from a post"""

    if not g.user:
        flash('Access unauthorized', 'danger')
        return redirect(url_for('posts.home'))

    user = User.query.get_or_404(user_id)

    # if not public + not the logged in user, prevent access
    if not user.favorites_public and g.user.id != user.id:
        return redirect(url_for('posts.home'))

    favorited_songs = (FavoritedSong
                       .query
                       .filter(FavoritedSong.user_id == user.id)
                       .order_by(FavoritedSong.timestamp.desc())
                       .all())

    return render_template('users/favorited.html', user=user, favorited_songs=favorited_songs)

@users_bp.route('/toggle_favorites_public', methods=['POST'])
def toggle_favorites_public():

    do_authorize()

    # if toggled true, then false, vice versa
    g.user.favorites_public = not g.user.favorites_public
    db.session.commit()

    return redirect(url_for('users.show_favorited_songs', user_id=g.user.id))