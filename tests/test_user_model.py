# test_user_repr
# test_user_model
# test_user_signup
# test_duplicate_username_signup
# test_user_authenticate
# test_user_signup_with_defaults
# test_favorites_public
# test_user_deletion
import os
from unittest import TestCase
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError

os.environ['DATABASE_URL'] = 'postgresql:///imagime_test_db'

from app import app
from models import db, User, Post, Song, PostSong, FavoritedSong
from flask_bcrypt import Bcrypt


app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_ECHO'] = False


bcrypt = Bcrypt()

class ModelTestCase(TestCase):
    """Test all model methods and relationships"""

    def setUp(self):
        """Create test client + add sample data"""

        with app.app_context():
            db.drop_all()
            db.create_all()

            self.client = app.test_client()

            # Create a sample user
            self.u1 = User.signup(username="user1",
                                  email="u1@test.com",
                                  password="password",
                                  profile_img=None)
            self.u1.id = 111

            self.u2 = User.signup(username="user2",
                                  email="u2@test.com",
                                  password="password",
                                  profile_img=None)
            self.u2.id = 222

            db.session.commit()

            # create sample posts
            self.p1 = Post(user_id=self.u1.id,
                           image='/static/test1.png',
                           description='Test Post 1')
            self.p2 = Post(user_id=self.u2.id,
                           image='/static/test2.png',
                           description='Test Post 2')

            db.session.add_all([self.p1, self.p2])
            db.session.commit()

            # create sample songs
            self.s1 = Song(title='Test Song 1',
                           artist='Test Artist 1',
                           image_url='https://test.com/album1.jpg',
                           spotify_url='https://test.com/song1',
                           preview_url='https://test.com/preview1.mp3')
            self.s2 = Song(title='Test Song 2',
                           artist='Test Artist 2',
                           image_url='https://test.com/album2.jpg',
                           spotify_url='https://test.com/song2',
                           preview_url='https://test.com/preview2.mp3')

            db.session.add_all([self.s1, self.s2])
            db.session.commit()

            # associate song with the post
            post_song_1 = PostSong(post_id=self.p1.id, song_id=self.s1.id)
            post_song_2 = PostSong(post_id=self.p2.id, song_id=self.s2.id)

            db.session.add_all([post_song_1, post_song_2])
            db.session.commit()

            # reattach users
            self.u1 = User.query.get(self.u1.id)
            self.u2 = User.query.get(self.u2.id)

            # reattach the posts
            self.p1 = Post.query.get(self.p1.id)
            self.p2 = Post.query.get(self.p2.id)

            # reattach the songs
            self.s1 = Song.query.get(self.s1.id)
            self.s2 = Song.query.get(self.s2.id)

    def tearDown(self):
        """Clean up after each test"""

        with app.app_context():
            response = super().tearDown()
            db.session.rollback()
            return response

    ########################### User Model Tests ################################

    def test_user_repr(self):
        """Test user __repr__"""

        expected_repr = f'<User id={self.u1.id} username={self.u1.username}, email={self.u1.email}>'
        self.assertEqual(repr(self.u1), expected_repr)

    def test_user_model(self):
        """Does the basic user model work?"""

        user = User.query.get(self.u1.id)

        self.assertEqual(user.username, 'user1')
        self.assertEqual(user.email, 'u1@test.com')

    def test_user_signup(self):
        """Can we sign up a new user?"""

        new_user = User.signup(username='newuser',
                               email='newuser@test.com',
                               password='password',
                               profile_img=None)

        db.session.add(new_user)
        db.session.commit()

        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(User.query.count(), 3)

    def test_duplicate_username_signup(self):
        """Test that no two users can sig up with the same username"""

        with self.assertRaises(IntegrityError):
            User.signup(username='user1',
                        email='u3@test.com',
                        password='password',
                        profile_img=None)

            db.session.commit()

    def test_user_authenticate(self):
        """Is a user authenticate with valid credentials?"""

        user = User.authenticate('user1', 'password')

        self.assertIsNotNone(user)
        self.assertTrue(bcrypt.check_password_hash(user.password, 'password'))
        self.assertFalse(User.authenticate('user1', 'wrongpassword'))

    def test_user_signup_with_defaults(self):
        """Test user creation with default values for optional fields"""

        user = User.signup(username='newuser',
                           email='newuser@test.com',
                           password='password',
                           profile_img=None)

        db.session.add(user)
        db.session.commit()

        self.assertEqual(user.profile_img, '/static/images/assets/default-pic.png')


    def test_favorites_public(self):
        """Test that the visibility of a users favorited songs are set to False by default"""


        self.assertFalse(self.u1.favorites_public)

    def test_user_deletion(self):
        """Test user deletion"""

        user = User.query.get(self.u1.id)
        db.session.delete(user)
        db.session.commit()

        self.assertIsNone(User.query.get(self.u1.id))
        self.assertEqual(FavoritedSong.query.filter_by(user_id=self.u1.id).count(), 0)
