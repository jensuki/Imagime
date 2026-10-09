"""Upload regressions using an isolated database and mocked external APIs.

Run: venv/bin/python -m unittest discover -s tests -p test_post_song_upload.py
"""

import io
import os
import tempfile
from unittest import TestCase
from unittest.mock import patch

from flask import Flask, g
from models import db, User, Post, Song, PostSong

with patch.dict(os.environ, {'SPOT_CLIENT_ID': 'test', 'SPOT_API_KEY': 'test'}):
    from blueprints.posts.routes import posts_bp


class PostSongUploadTestCase(TestCase):
    def setUp(self):
        self.upload_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.upload_dir.cleanup)
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY='test',
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI='sqlite://',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            UPLOAD_FOLDER=self.upload_dir.name,
        )
        db.init_app(self.app)
        self.app.register_blueprint(posts_bp)
        self.context = self.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        self.addCleanup(db.session.remove)
        db.create_all()
        user = User(username='upload-test', email='upload@example.com', password='test')
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id

        @self.app.before_request
        def authenticate():
            g.user = User.query.get(self.user_id)

        self.client = self.app.test_client()

    def track(self, number, preview=None):
        return dict(
            title='Track {}'.format(number), artist='Artist',
            spotify_url='https://open.spotify.com/track/{}'.format(number),
            preview_url=preview,
        )

    def upload(self, tracks, use_file=False):
        data = {'description': 'Upload regression'}
        if use_file:
            data['image_file'] = (io.BytesIO(b'mocked image'), 'test.jpg')
        else:
            data['image_url'] = 'https://example.com/image.jpg'
        with patch('blueprints.posts.routes.image_to_keywords', return_value=['music']), \
                patch('blueprints.posts.routes.keywords_to_songs', return_value=tracks):
            response = self.client.post('/posts/new', data=data)
        self.assertEqual(response.status_code, 302)
        post = Post.query.order_by(Post.id.desc()).first()
        self.assertIsNotNone(post)
        self.assertTrue(response.location.endswith('/posts/{}'.format(post.id)))
        return post

    def test_missing_previews_keep_distinct_tracks_for_url_and_file(self):
        for use_file in (False, True):
            with self.subTest(use_file=use_file):
                post = self.upload([self.track(1), self.track(2)], use_file=use_file)
                self.assertEqual({song.spotify_url for song in post.songs}, {
                    self.track(1)['spotify_url'], self.track(2)['spotify_url'],
                })
                self.assertEqual(PostSong.query.filter_by(post_id=post.id).count(), 2)
        self.assertEqual(Song.query.count(), 2)

    def test_shared_preview_keeps_distinct_tracks(self):
        preview = 'https://example.com/shared.mp3'
        post = self.upload([self.track(1, preview), self.track(2, preview)])
        self.assertEqual(len(post.songs), 2)
        self.assertEqual(PostSong.query.filter_by(post_id=post.id).count(), 2)

    def test_repeated_track_is_linked_once(self):
        track = self.track(1)
        post = self.upload([track, track, self.track(2), track])
        self.assertEqual(Song.query.count(), 2)
        self.assertEqual(PostSong.query.filter_by(post_id=post.id).count(), 2)

    def test_existing_track_is_reused_when_preview_changes(self):
        existing = Song(**self.track(1, 'https://example.com/old.mp3'))
        db.session.add(existing)
        db.session.commit()
        post = self.upload([self.track(1, 'https://example.com/new.mp3')])
        self.assertEqual([song.id for song in post.songs], [existing.id])
        self.assertEqual(Song.query.count(), 1)
        self.assertEqual(existing.preview_url, 'https://example.com/new.mp3')

    def test_missing_preview_is_filled_by_later_recommendation(self):
        self.upload([self.track(1)])
        post = self.upload([self.track(1, 'https://example.com/preview.mp3')])
        self.assertEqual(Song.query.count(), 1)
        self.assertEqual(post.songs[0].preview_url, 'https://example.com/preview.mp3')
        self.upload([self.track(1)])
        self.assertEqual(Song.query.first().preview_url, 'https://example.com/preview.mp3')
