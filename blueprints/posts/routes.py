import os
from flask import Blueprint, render_template, redirect, request, flash, session, g, url_for, jsonify, current_app
from models import db, User, Post, Song, FavoritedSong, PostSong
from forms import AddImageForm
from utils.helpers import do_login, do_logout, do_authorize
from api_helpers import image_to_keywords, keywords_to_songs
from werkzeug.utils import secure_filename
from datetime import datetime


CURR_USER_KEY = 'curr_user'

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/')
def home():
    print('HOME ROUTE ACCESSED')
    """
    Display home page if user is logged in
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

@posts_bp.route('/posts/new', methods=['GET', 'POST'])
def add_post():
    """Adding a new poste"""

    if g.user is None:
        flash('You must be logged in to create a post', 'danger')
        return redirect(url_for('users.login'))

    form = AddImageForm()

    keywords = None
    songs = None
    image_path = None

    if form.validate_on_submit():
        image_url = form.image_url.data
        image_file = form.image_file.data
        description = form.description.data

        try:
            if image_url:
                keywords = image_to_keywords(image_url=image_url)
                image_path = image_url

            elif image_file:
                # save the uploaded image file
                filename = secure_filename(image_file.filename)
                image_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_save_path)

                # open the saved image file and pass it to 'image_to_keywords'
                keywords = image_to_keywords(local_image_file=image_save_path)
                image_path = url_for('static', filename=f'images/uploads/{filename}')

            if keywords:
                songs = keywords_to_songs(keywords)
            else:
                flash('No keywords found', 'warning')
                songs = []

            # proceed to add new image post to DB
            new_post = Post(
                user_id=g.user.id,
                image=image_path,
                description=description
            )
            db.session.add(new_post)
            db.session.flush()

            for song in songs:
                existing_song = Song.query.filter_by(preview_url=song['preview_url']).first()
                if not existing_song:
                    # add new song to the DB
                    existing_song = Song(
                        title=song['title'],
                        artist=song['artist'],
                        spotify_url=song.get('spotify_url'),
                        image_url=song.get('image_url'),
                        preview_url=song.get('preview_url')
                    )
                    db.session.add(existing_song)
                    db.session.flush()

                    # check if post-song association already exists
                    post_song_exists = PostSong.query.filter_by(post_id=new_post.id, song_id=existing_song.id).first()
                    if not post_song_exists:
                        # associate post with songs if not already associated
                        post_song = PostSong(post_id=new_post.id, song_id=existing_song.id)
                        db.session.add(post_song)

            db.session.commit()
            flash('Post successfully added!', 'success')
            return redirect(url_for('posts.show_post', post_id=new_post.id))

        except Exception as e:
            flash(f'An error occured: {e}', 'error')
            db.session.rollback()
            return redirect(url_for('posts.home'))

    return render_template('posts/new.html', form=form, keywords=keywords, songs=songs)

@posts_bp.route('/users/<int:user_id>/posts', methods=['GET'])
def user_posts(user_id):
    """Display all posts made my a specific user"""

    if g.user is None:
        flash('Please log in to view this page', 'danger')
        return redirect(url_for('users.login'))

    user = User.query.get_or_404(user_id)

    posts = (Post
             .query
             .filter(Post.user_id == user_id)
             .order_by(Post.timestamp.desc())
             .all())

    return render_template('users/posts.html', user=user, posts=posts)

@posts_bp.route('/posts/<int:post_id>', methods=['GET'])
def show_post(post_id):
    """Display post details with the generated songs"""

    post = Post.query.get_or_404(post_id)
    user = User.query.get_or_404(post.user_id)

    # get offset from request or default to 0
    offset = request.args.get('offset', 0, type=int)
    limit = 5 # num songs to load per batch

    songs = (Song
             .query
             .join(PostSong)
             .filter(PostSong.post_id == post_id)
             .offset(offset)
             .limit(limit)
             .all())

    # check if the user is logged in and gather favorited songs
    favorited_song_ids = []
    if g.user:
        favorited_song_ids = [fav.song_id for fav in g.user.favorited_songs]

    # return JSON if `json` query parameter is present
    if request.args.get('json'):
        return jsonify({
            'songs': [
                {
                    'title': song.title,
                    'artist': song.artist,
                    'preview_url': song.preview_url,
                    'image_url': song.image_url,
                    'id': song.id,
                    'spotify_url': song.spotify_url,
                    'is_favorited': song.id in favorited_song_ids,
                } for song in songs
            ]
        })


    # return the full template for the initial load
    return render_template(
        'posts/detail.html',
        post=post,
        user=user,
        songs=songs,
        favorited_song_ids=favorited_song_ids,
        offset=offset + limit,

    )

@posts_bp.route('/posts/<int:post_id>/songs/<int:song_id>/favorite', methods=['POST'])
def add_favorite(post_id, song_id):
    """Add song(s) to user's favorites"""

    if not g.user:
        flash('Access unauthorized', 'danger')
        return redirect(url_for('posts.home'))

    # ensure post amd song exists
    post = Post.query.get_or_404(post_id)
    song = Song.query.get_or_404(song_id)

    # check if song has already been favorited
    favorite = FavoritedSong.query.filter_by(
        user_id=g.user.id,
        post_id=post_id,
        song_id=song_id).first()

    if favorite:
        # then remove from favorites
        db.session.delete(favorite)
    else:
        new_favorite = FavoritedSong(
            user_id=g.user.id,
            post_id=post_id,
            song_id=song_id,
            timestamp=datetime.utcnow())

        db.session.add(new_favorite)

    db.session.commit()

    return redirect(url_for('posts.show_post', post_id=post_id))

@posts_bp.route('/favorites/<int:song_id>/remove', methods=['POST'])
def remove_favorite(song_id):
    """Remove a song from user's favorites"""

    do_authorize()

    # find the favorited song entry for current user
    favorite = FavoritedSong.query.filter_by(user_id=g.user.id, song_id=song_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()

    return redirect(url_for('users.show_favorited_songs', user_id=g.user.id))

@posts_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    """Delete post and set related favorited songs' post_id to NULL"""

    do_authorize()

    post = Post.query.get_or_404(post_id)

    if post.user_id != g.user.id:
        flash('Access unauthorized', 'danger')
        return redirect(url_for('posts.home'))

    # set post_id to null for other users who have saved songs from this post
    FavoritedSong.query.filter_by(post_id=post_id).update({'post_id': None})

    # delete related PostSong entriest o avoid orphaned records
    PostSong.query.filter_by(post_id=post_id).delete()

    # delete the post itself
    db.session.delete(post)
    db.session.commit()

    flash('Post deleted succesfully', 'success')
    return redirect(url_for('users.user_profile', user_id=g.user.id))