import os
from unittest import TestCase
from unittest.mock import patch
from app import g, app, CURR_USER_KEY
from models import db, User, Post, Song, PostSong, FavoritedSong
from api_helpers import image_to_keywords, keywords_to_songs

os.environ['DATABASE_URL'] = "postgresql:///imagime_test_db"

app.config['WTF_CSRF_ENABLED'] = False

class PostSongViewTestCase(TestCase):
    """Tests for user views, post views, song views, AJAX requests"""

    def setUp(self):
        """Pre-test set up with sample data"""
        with app.app_context():
            db.drop_all()
            db.create_all()

            self.client = app.test_client()

            # Create test users
            self.u1 = User.signup(username="user1",
                                  email='u1@test.com',
                                  password="password",
                                  profile_img=None)
            self.u1.id = 111

            self.u2 = User.signup(username="user2",
                                  email='u2@test.com',
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
            db.session.remove()


    def image_post_setup(self, image_to_keywords_mock, keywords_to_songs_mock):
        """Helper method to set up mock responses for image posting tests"""

        image_to_keywords_mock.return_value = ['keyword1', 'keyword2']
        keywords_to_songs_mock.return_value = [{
            'title': 'Test Song 1',
            'artist': 'Artist 1',
            'image_url': 'https://example.com/album1.jpg',
            'spotify_url': 'https://example.com/song1',
            'preview_url': 'https://example.com/preview1.mp3'
        },{
            'title': 'Test Song 2',
            'artist': 'Artist 2',
            'image_url': 'https://example.com/album2.jpg',
            'spotify_url': 'https://example.com/song2',
            'preview_url': 'https://example.com/preview2.mp3'
        },{
            'title': 'Test Song 2', # Duplicate Song
            'artist': 'Artist 2',
            'image_url': 'https://example.com/album2.jpg',
            'spotify_url': 'https://example.com/song2',
            'preview_url': 'https://example.com/preview2.mp3'
        }]

    @patch('blueprints.posts.routes.keywords_to_songs')
    @patch('blueprints.posts.routes.image_to_keywords')
    def test_add_post_image_url(self, image_to_keywords_mock, keywords_to_songs_mock):
        """Test that a logged-in user can create a new image URL post and mock API response"""

        self.image_post_setup(image_to_keywords_mock, keywords_to_songs_mock)

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        response = self.client.post('/posts/new', data={
            'image_url': 'https://fastly.picsum.photos/id/171/2048/1536.jpg?hmac=16eVtfmqTAEcr8VwTREQX4kV8dzZKcGWI5ouMlhRBuk',
            'description': 'New test post'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        # Check flash messages before the redirect
        with self.client.session_transaction() as sess:
            flash_messages = sess['_flashes']
            self.assertIn(('success', 'Post successfully added!'), flash_messages)

        response = self.client.get(response.location, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('New test post', str(response.data))


    @patch('blueprints.posts.routes.keywords_to_songs')
    @patch('blueprints.posts.routes.image_to_keywords')
    def test_add_post_image_file(self, image_to_keywords_mock, keywords_to_songs_mock):
        """Test that a logged in user can post an image and mock API responses"""

        self.image_post_setup(image_to_keywords_mock, keywords_to_songs_mock)

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u2.id

        # simulate file upload by providing file-like object
        image_path = os.path.join(os.getcwd(), 'tests', 'test_image.jpg')
        with open(image_path, 'rb') as img:
            data = {
                'image_file': (img, 'test_image.jpg'),
                'description': "New test post with local image file"
            }

            response = self.client.post('/posts/new',
                                        data=data,
                                        content_type='multipart/form-data',
                                        follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('New test post with local image file', str(response.data))


    def test_display_post(self):
        """Test that a logged in user can view their posts as well as other users"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        response = self.client.get(f'/users/{self.u1.id}/posts')
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Post 1', html)

        # view another users posts as u1
        response = self.client.get(f'/users/{self.u2.id}/posts')
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Post 2', html)

    def test_add_post_no_image(self):
        """Test that a post cannot be created without an image URL or file."""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        # Post data with neither image URL nor file, which should trigger the ValueError in the actual function
        response = self.client.post('/posts/new', data={
            'image_url': '',
            'description': 'Test post with invalid image'
        }, follow_redirects=True)

        # Check that the correct error message is flashed
        self.assertEqual(response.status_code, 200)
        self.assertIn('You must provide an image URL or upload an image file', str(response.data))

    def test_view_post_unauthenticated(self):
        """Test that unauthenticated users are redirects when trying to view a post"""

        response = self.client.get(f'/users/{self.p1.id}/posts', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Please log in to view this page', str(response.data))
        self.assertIn('<h2 class="login_message">', str(response.data))

    def test_add_post_invalid_image_url(self):
        """Test that a post cannot be created with an invalid image URL."""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        response = self.client.post('/posts/new', data={
            'image_url': 'invalid-url',
            'description': 'Test post with invalid URL'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid URL.', str(response.data))

    def test_favorite_song(self):
        """Test that a logged in user can favorite a song from a post"""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        # favorite the song
        response = self.client.post(f'/posts/{self.p1.id}/songs/{self.s1.id}/favorite',
                                    follow_redirects=True)

        # verify that the song was added to their favorites
        favorited_song = FavoritedSong.query.filter_by(
                                        user_id=self.u1.id,
                                        post_id=self.p1.id,
                                        song_id=self.s1.id).first()
        self.assertIsNotNone(favorited_song)

        # unfavorite the song
        response = self.client.post(f'/posts/{self.p1.id}/songs/{self.s1.id}/favorite',
                                     follow_redirects=True)

        # verify removal of favorite
        favorited_song = FavoritedSong.query.filter_by(
                                        user_id=self.u1.id,
                                        post_id=self.p1.id,
                                        song_id=self.s1.id).first()
        self.assertIsNone(favorited_song)


    def test_delete_post_with_favorited_songs(self):
        """Test deleting a post that has songs which have been favorited."""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        # u1 favorites a song from their own post
        favorited_song_user1 = FavoritedSong(user_id=self.u1.id,
                                            post_id=self.p1.id,
                                            song_id=self.s1.id)
        db.session.add(favorited_song_user1)

        # u2 favorites a song from u1's post
        favorited_song_user2 = FavoritedSong(user_id=self.u2.id,
                                            post_id=self.p1.id,
                                            song_id=self.s1.id)
        db.session.add(favorited_song_user2)

        db.session.commit()

        # verify the song was favorited by both users
        favorited_song_user1 = FavoritedSong.query.filter_by(
            user_id=self.u1.id,
            post_id=self.p1.id,
            song_id=self.s1.id
        ).first()
        favorited_song_user2 = FavoritedSong.query.filter_by(
            user_id=self.u2.id,
            post_id=self.p1.id,
            song_id=self.s1.id
        ).first()

        self.assertIsNotNone(favorited_song_user1)
        self.assertIsNotNone(favorited_song_user2)

        # u1 deletes the post
        response = self.client.post(f'/posts/{self.p1.id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Post deleted successfully', str(response.data))

        # verify that u1's favorited song was removed
        favorited_song_user1 = FavoritedSong.query.filter_by(
            user_id=self.u1.id,
            post_id=self.p1.id,
            song_id=self.s1.id
        ).first()
        self.assertIsNone(favorited_song_user1)

        # verify that u2's favorited song still exists but with post_id set to None
        favorited_song_user2 = FavoritedSong.query.filter_by(
            user_id=self.u2.id,
            song_id=self.s1.id
        ).first()
        self.assertIsNotNone(favorited_song_user2)

    def test_delete_post(self):
        """Test that a logged-in user can delete their post."""

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u2.id

        response = self.client.post(f'/posts/{self.p2.id}/delete', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Post deleted successfully', str(response.data))

        deleted_post = Post.query.get(self.p2.id)
        self.assertIsNone(deleted_post)


    ################ PostSong Views ######################

    def test_display_post_with_associated_songs(self):
        """Test that a logged in user can view all the songs related to a post """

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u2.id

        # access post detail page
        response = self.client.get(f'/posts/{self.p2.id}')
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Song 2', html)


    @patch('blueprints.posts.routes.keywords_to_songs')
    @patch('blueprints.posts.routes.image_to_keywords')
    def test_unique_post_song_association(self, image_to_keywords_mock, keywords_to_songs_mock):
        """Test that a song cannot be associated with the same post more than once."""

        self.image_post_setup(image_to_keywords_mock, keywords_to_songs_mock)

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.u1.id

        # make the post request
        response = self.client.post('/posts/new', data={
            'image_url': 'https://test.com/test_image.jpg',
            'description': "Test post with duplicate songs"
        }, follow_redirects=True)

        # fetch the post from the database
        new_post = Post.query.filter_by(description='Test post with duplicate songs').first()
        self.assertIsNotNone(new_post)

        # verify the songs associated with the post
        unique_songs = set((song.title, song.artist) for song in new_post.songs)

        self.assertEqual(len(unique_songs), 2)  # There should be only 2 unique songs, not 3
        self.assertEqual(len(new_post.songs), 2)  # Should only count unique songs
