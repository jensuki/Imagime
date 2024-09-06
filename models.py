from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

bcrypt = Bcrypt()
db = SQLAlchemy

class User(db.Model):
    """User model instance"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    bio = db.Column(db.Text)
    profile_img = db.Column(db.Text, default='/static/images/assets/default-pic.png')
    password = db.Column(db.String, nullable=False)
    favorites_public = db.Column(db.Boolean, default=False)

    # 1:M relationship from user --< posts (user.posts)(post.user)
    posts = db.relationship('Post', backref='user', cascade='all, delete-orphan')

    # M:M relationship from user --< favorited_songs (user.favorited_songs)(favorited_songs.user)
    favorited_songs = db.relationship('FavoritedSong', backref='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User id={self.id} username={self.username}, email={self.email}>"

    @classmethod
    def signup(cls, username, email, password, profile_img):
        """
        Sign up method for user
        Hashes password and adds user to DB

        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            profile_img=profile_img or '/static/images/assets/default-pic.png'
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """
        Authenticate user with their 'username' & 'password'
        If found, return that user object, else returun False

        """

        user = cls.query.filter_by(username-username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Post(db.Model):
    """Post model instance"""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    # M:M relationship between posts and songs via PostSong (post.songs)(song.posts)
    # when post is deleted -> all PostSong entries are deleted
    songs = db.relationship('Song', secondary='postsongs', backref='posts', cascade='all, delete')

    def __repr__(self):
        return f"<Post id={self.id} user_id={self.user_id} image={self.image}>"

class Song(db.Model):
    """Song model instance"""

    __tablename__ = "songs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.Text)
    spotify_url = db.Column(db.Text, nullable=False)
    preview_url = db.Column(db.Text)

    def __repr__(self):
        return f"<Song id={self.id} title={self.title} artist={self.artist}>"

class PostSong(db.Model):
    """
    Post-Song mapping model:
    Association table between posts and songs
    (Users can revisit posts / favorite songs)

    """

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)

    # unique constraint to ensure same song cnanot be associated with same post 1+
    __table_args__ = (
        db.UniqueConstraint('post_id', 'song_id', name='unique_post_song'),
    )

    def __repr__(self):
        return f"<PostSong id={self.id} post_id={self.post_id} song_id={self.song_id}>"

class FavoritedSong(db.Model):
    """Links user to their favorited songs"""

    __tablename__ = "favorited_songs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)

    # make post_id nullable if post with a favorited song gets deleted
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), ondelete='SET NULL', nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)

    song = db.relationship('Song', backref='favorited_songs')
    post = db.relationship('Post', backref='favorited_songs')

def connect_db(app):
    """Connect DB + app"""

    db.app = app
    db.init_app(app)