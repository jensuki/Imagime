# test_post_repr
# test_post_creation
# test_post_without_image
# test_display_post
# test_post_deletion
# test_post_user_relationship
# test_post_creation_with_mocked_apis
# test_post_song_relationship
# test_favoriting_song
# test_unfavoriting_song
# test_post_deletion_removes_postsong_associations
# test_display_favorited_songs
# test_post_deletion_removes_favorited_songs
# test_favorited_song_relationship

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

    ########################  Post Models #######################

    def test_post_repr(self):
        """Test post] __repr__"""

        # create post
        post = Post(user_id=self.u1.id,
                    image='test_image.png',
                    description='Test Post')

        db.session.add(post)
        db.session.commit()

        expected_repr = f"<Post id={post.id} user_id={post.user.id} image={post.image}>"
        self.assertEqual(repr(post), expected_repr)

    def test_post_creation(self):
        """Test creating a post"""

        post = Post(user_id=self.u1.id,
                    image='/static/test3.png',
                    description='Test Post 3')

        db.session.add(post)
        db.session.commit()

        self.assertEqual(Post.query.count(), 3)

    def test_post_without_image(self):
        """Test creating a post without an image"""

        with self.assertRaises(IntegrityError):
            post = Post(user_id=self.u1.id,
                        description='Post without an image')

            db.session.add(post)
            db.session.commit()

    def test_display_post(self):
        """Test displaying a post"""
        post = Post.query.get(self.p1.id)

        self.assertEqual(post.image, '/static/test1.png')
        self.assertEqual(Post.query.count(), 2)

    def test_post_deletion(self):
        """Test the deletion of a post"""

        db.session.delete(self.p1)
        db.session.commit()
        self.assertIsNone(Post.query.get(self.p1.id))

    def test_post_user_relationship(self):
        """Test the relationship between post & user"""

        post = Post.query.get(self.p1.id)

        self.assertEqual(post.user.id, self.u1.id)
        self.assertEqual(post.user.username, self.u1.username)
        self.assertTrue(len(post.user.posts) > 0)



    ########################  Post Song Models #######################

    @patch('blueprints.posts.routes.image_to_keywords')
    @patch('blueprints.posts.routes.keywords_to_songs')
    def test_post_creation_with_mocked_apis(self, mock_keywords_to_songs, mock_image_to_keywords):
        """Test post creation with mocked API responses"""

        # Mock API responses
        mock_image_to_keywords.return_value = ['keyword1', 'keyword2']
        mock_keywords_to_songs.return_value = [
            {'title': 'Mocked Song 1', 'artist': 'Mocked Artist 1', 'image_url': 'http://mock.com/1', 'spotify_url': 'http://mock.com/1', 'preview_url': 'http://mock.com/1.mp3'},
            {'title': 'Mocked Song 2', 'artist': 'Mocked Artist 2', 'image_url': 'http://mock.com/2', 'spotify_url': 'http://mock.com/2', 'preview_url': 'http://mock.com/2.mp3'}
        ]

        post = Post(user_id=self.u1.id,
                    image='/static/test3.png',
                    description='Test Post 3')

        db.session.add(post)
        db.session.commit()

        # Simulate calling the API helpers
        keywords = mock_image_to_keywords(post.image)
        songs = mock_keywords_to_songs(keywords)

        for song_data in songs:
            song = Song(**song_data)
            db.session.add(song)
            db.session.commit()
            post_song = PostSong(post_id=post.id, song_id=song.id)
            db.session.add(post_song)

        db.session.commit()

        # Check that the post has been created and associated with the mocked songs
        self.assertEqual(len(post.songs), 2)
        self.assertEqual(post.songs[0].title, 'Mocked Song 1')
        self.assertEqual(post.songs[1].title, 'Mocked Song 2')

    def test_post_song_relationship(self):
        """Test the relationship between post and songs"""

        post = Post.query.get(self.p1.id)

        # Assert that post has the correct number of associated songs
        self.assertEqual(len(post.songs), 1)
        self.assertEqual(post.songs[0].title, self.s1.title)

        post_song = PostSong.query.filter_by(post_id=self.p1.id, song_id=self.s1.id).first()

        self.assertIsNotNone(post_song)
        self.assertEqual(post_song.post_id, self.p1.id)
        self.assertEqual(post_song.song_id, self.s1.id)


    ####################### Favorite Models ########################

    def test_favoriting_song(self):
        """Test favoriting a song by a user"""

        favorited_song = FavoritedSong(user_id=self.u1.id, song_id=self.s1.id)
        db.session.add(favorited_song)
        db.session.commit()

        self.assertTrue(FavoritedSong.query.filter_by(user_id=self.u1.id, song_id=self.s1.id).first())

    def test_unfavoriting_song(self):
        """Test unfavoriting a song by a user"""

        favorited_song = FavoritedSong(user_id=self.u1.id, song_id=self.s1.id)
        db.session.add(favorited_song)
        db.session.commit()

        db.session.delete(favorited_song)
        db.session.commit()

        self.assertIsNone(FavoritedSong.query.filter_by(user_id=self.u1.id, song_id=self.s1.id).first())

    def test_post_deletion_removes_postsong_associations(self):
        """Test that deleting a post also removes associated PostSong entries"""

        db.session.delete(self.p1)
        db.session.commit()

        self.assertEqual(PostSong.query.filter_by(post_id=self.p1.id).count(), 0)

    def test_display_favorited_songs(self):
        """Test the display of favorited songs"""

        favorited_song = FavoritedSong(user_id=self.u1.id, song_id=self.s1.id)

        db.session.add(favorited_song)
        db.session.commit()

        user = User.query.get(self.u1.id)
        self.assertEqual(len(user.favorited_songs), 1)
        self.assertEqual(user.favorited_songs[0].song_id, self.s1.id)

    def test_post_deletion_removes_favorited_songs(self):
        """Test that deleting a post sets the post_id to NULL in related favorited songs."""

        # Create a favorited song associated with the post
        favorited_song = FavoritedSong(user_id=self.u1.id, song_id=self.s1.id, post_id=self.p1.id)
        db.session.add(favorited_song)
        db.session.commit()

        # First, remove the post-song associations
        PostSong.query.filter_by(post_id=self.p1.id).delete()

        # delete the post
        db.session.delete(self.p1)
        db.session.commit()

        # Fetch the favorited song again
        favorited_song_after = FavoritedSong.query.filter_by(user_id=self.u1.id, song_id=self.s1.id).first()


        # Check if post_id is set to NULL and song_id remains intact
        self.assertIsNotNone(favorited_song_after)
        self.assertIsNone(favorited_song_after.post_id)
        self.assertEqual(favorited_song_after.song_id, self.s1.id)

    def test_favorited_song_relationship(self):
        """Test relationshp between favorites and songs"""

        # create new favoritedsong record linking user to a song they like
        favorited_song = FavoritedSong(user_id=self.u1.id, song_id=self.s1.id)
        db.session.add(favorited_song)
        db.session.commit()

        # retrieve that favorited record
        favorited = FavoritedSong.query.filter_by(user_id=self.u1.id, song_id=self.s1.id).first()

        self.assertIsNotNone(favorited)
        self.assertEqual(favorited.user_id, self.u1.id)
        self.assertEqual(favorited.song_id, self.s1.id)