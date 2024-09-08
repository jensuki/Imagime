import requests
from unittest import TestCase
from unittest.mock import patch, Mock
from api_helpers import image_to_keywords, keywords_to_songs

class EpixTestCase(TestCase):
    """Test that image_to_keywords method is properly integrated"""

    @patch('api_helpers.requests.get')
    @patch('api_helpers.requests.post')
    def test_image_to_keywords(self, mock_get, mock_post):
        """Test that image_to_keywords method extract correct keywords from image posts"""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ok',
            'keywords': [
                {'keyword': 'rain'},
                {'keyword': 'weather'},
                {'keyword': 'cityscape'}
            ]
        }

        # mimic mock responses
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response

        keywords = image_to_keywords('/tests/test_image.jpg')

        self.assertEqual(keywords, ['rain', 'weather', 'cityscape'])
        self.assertIsNotNone(keywords)
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)

    @patch('api_helpers.random.shuffle', lambda x: None) # don't randomize in mock
    @patch('api_helpers.sp.search')
    def test_keywords_to_songs(self, mock_search):
        """Test that keywords_to_songs method correctly maps keywords to Spotipy tracks"""

        mock_search.return_value = {
            'tracks': {
                'items': [
                    {
                        'name': 'Rainy Day',
                        'artists': [{'name': 'Artist 1'}],
                        'album': {'name': 'A Rainy Album',
                                  'images': [{ 'url': 'https://test.com/album1.jpg'}]},
                        'external_urls': {'spotify': 'https://test.com/song1'},
                        'preview_url': 'https://test.com/preview1.mp3'
                    },
                    {
                        'name': 'City Lights',
                        'artists': [{'name': 'Artist 2'}],
                        'album': {'name': 'City Album',
                                  'images': [{'url': 'https://test.com/album2.jpg'}]},
                        'external_urls': {'spotify': 'https://test.com/song2'},
                        'preview_url': 'https://test.com/preview2.mp3'
                    }

                ]
            }
        }

        songs = keywords_to_songs(['rain', 'weather', 'cityscape'])

        self.assertEqual(len(songs), 2)
        self.assertEqual(songs[0]['title'], 'Rainy Day')
        self.assertEqual(songs[0]['artist'], 'Artist 1')
        self.assertEqual(songs[1]['title'], 'City Lights')
        self.assertEqual(songs[1]['artist'], 'Artist 2')
        self.assertIsNotNone(songs)
        self.assertIsInstance(songs, list)
        self.assertGreater(len(songs), 0)


    @patch('api_helpers.random.shuffle', lambda x: None) # don't randomize in mock
    @patch('api_helpers.sp.search')
    def test_keywords_to_songs_no_results(self, mock_search):
        """Test that keywords_to_songs handles no results."""

        mock_search.return_value = {'tracks': {'items': []}}

        songs = keywords_to_songs(['no data'])
        self.assertEqual(songs, [])