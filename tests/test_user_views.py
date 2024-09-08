import os
from unittest import TestCase
from unittest.mock import patch
from app import g, app, CURR_USER_KEY
from models import db, User, Post, Song, PostSong, FavoritedSong

os.environ['DATABASE_URL'] = "postgresql:///imagime_test_db"

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Tests for user views, post views, song views, AJAX requests"""

    def setUp(self):
        """Pre-test set up with sample data"""
        with app.app_context():
            db.drop_all()
            db.create_all()

            self.client = app.test_client()

            # Create a test user
            self.u1 = User.signup(username="user1",
                                  email='u1@test.com',
                                  password="password",
                                  profile_img=None)
            self.u1.id = 111  # Ensure ID is set before committing

            # Create a test user
            self.u2 = User.signup(username="user2",
                                  email='u2@test.com',
                                  password="password",
                                  profile_img=None)
            self.u2.id = 222  # Ensure ID is set before committing

            db.session.commit()

            # Reload the user from the session to ensure it's attached
            self.u1 = User.query.get(self.u1.id)
            self.u2 = User.query.get(self.u2.id)

    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()

    #################### User Views ###############################

    def test_signup(self):
        """Test that a user can successfully sign up"""

        response = self.client.post('/signup', data={
            'username': 'newtestuser',
            'email': 'newuser@test.com',
            'password': 'password',
            'profile_img': None
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        new_user = User.query.filter_by(username="newtestuser").first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, 'newuser@test.com')

        with self.client.session_transaction() as sess:
            self.assertEqual(sess[CURR_USER_KEY], new_user.id)

    def test_failed_signup(self):
        """Test that user signup fails if non-unique username"""

        # Use an existing username
        self.u2 = User.signup(username='blue',
                              email='blue@blue.com',
                              password='password',
                              profile_img=None)
        db.session.commit()

        response = self.client.post('/signup', data={
            'username': 'blue',
            'email': 'blue@blue.com',
            'password': 'password',
            'profile_img': None
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Username or email already taken', response.data)

    def test_login(self):
        """Test that a user can successfully log in with their credentials"""

        response = self.client.post('/login', data={
            'username': self.u1.username,  # Using the username from setup
            'password': 'password'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, user1', response.data)

        with self.client.session_transaction() as sess:
            self.assertEqual(sess[CURR_USER_KEY], self.u1.id)

    def test_failed_login(self):
        """Test that a user cannot login with invalid credetials"""

        response = self.client.post('/login', data={
            'username': self.u1.username,
            'password': 'wrongpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid credentials", response.get_data(as_text=True))

    def test_logout(self):
        """Test that a user can successfully log out"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        response = self.client.get('/logout')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://localhost/login')

        response = self.client.get('/login', follow_redirects=True)
        # upon arriving at redirected page
        self.assertIn(b'You have successfully logged out', response.data)

        with self.client.session_transaction() as sess:
            self.assertNotIn(CURR_USER_KEY, sess)


    def test_logged_in_homepage(self):
        """Test home page for logged in users"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        # user has no posts
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("No posts to display", response.get_data(as_text=True))

        # user has posts
        post = Post(user_id=self.u1.id, image='test_image.jpg', description='Test Post')
        db.session.add(post)
        db.session.commit()

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Post', response.get_data(as_text=True))
        self.assertIn('test_image.jpg', response.get_data(as_text=True))

    def test_home_anonymous(self):
        """Test home page for an anonymous user"""

        with self.client.session_transaction() as sess:
            sess.pop(CURR_USER_KEY, None)

        response  = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Join Imagime today and capture moments in sound.", str(response.data))

    def test_user_profile(self):
        """Test viewing any users profile card"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        response = self.client.get(f'/users/{self.u2.id}')

        self.assertEqual(response.status_code, 200)
        self.assertIn(f'@{self.u2.username}', response.data.decode('utf-8'))

    def test_user_search(self):
        """Test searching for users thorough search form"""

        response = self.client.get('/users?q=user')

        response_data = response.data.decode('utf-8')

        self.assertIn('user1', response_data)
        self.assertIn('user2', response_data)
        self.assertNotIn('user3', response_data)

    def test_user_posts(self):
        """Test that a logged in user can view their posts and others posts"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u2.id

        # create post for u2
        post = Post(
            user_id=self.u2.id,
            image='test_image.jpg',
            description='Test Image Post')

        db.session.add(post)
        db.session.commit()

        response = self.client.get(f'/users/{self.u2.id}/posts')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Image Post', response.get_data(as_text=True))
        self.assertIn('test_image.jpg', response.get_data(as_text=True))

    def test_edit_profile(self):
        """Test editing a logged in users own profile"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        response = self.client.post('/users/profile', data={
            'username': 'updateduser1',
            'email': 'updatedu1@test.com',
            'password': 'password'
        }, follow_redirects=True)

        self.assertTrue(response.status_code, 200)
        user = User.query.get(self.u1.id)
        self.assertEqual(user.username, 'updateduser1')
        self.assertEqual(user.email, 'updatedu1@test.com')

    def test_delete_profile(self):
        """Test deleting a user profile."""

        user = User.query.get(self.u1.id)
        db.session.delete(user)
        db.session.commit()

        self.assertIsNone(User.query.get(self.u1.id))

    def test_view_public_favorited_songs(self):
        """Test that a logged-in user can view another user's public favorited songs."""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        # toggle the favorites to public via form submission
        response = self.client.post('/toggle_favorites_public', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # refetch the user to ensure the change is persisted
        user1 = User.query.get(self.u1.id)

        self.assertTrue(user1.favorites_public)

        # create new song
        song = Song(
            title="Test Song",
            artist="Test Artist",
            image_url="http://example.com/image.jpg",
            spotify_url="http://example.com",
            preview_url="http://example.com/preview.mp3")
        db.session.add(song)
        db.session.commit()

        # u1 favorites the song
        favorited_song = FavoritedSong(user_id=user1.id, song_id=song.id)
        db.session.add(favorited_song)
        db.session.commit()

        # log in as u2
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u2.id

        # refetch u1
        self.u1 = User.query.get(self.u1.id)

        # try to access u1's favorites
        response = self.client.get(f'/users/{self.u1.id}/favorited', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Song", response.get_data(as_text=True))
        self.assertIn('<div class="audio-player">', response.get_data(as_text=True))


    def test_hide_private_favorited_songs(self):
        """Test that a user's favorited songs are not displayed to other users if set to private."""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        # set u2's favorites to private
        self.u2.favorites_public = False

        db.session.commit()

        response = self.client.get(f'/users/{self.u2.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('<div class="audio-player">', str(response.data))  # Assuming this text is on the page
        self.assertIn('Private', str(response.data))