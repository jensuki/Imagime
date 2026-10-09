"""Preview helper failures must be visible without failing the image upload."""
import os
import subprocess
from unittest import TestCase
from unittest.mock import patch

with patch.dict(os.environ, {'SPOT_CLIENT_ID': 'test', 'SPOT_API_KEY': 'test'}):
    from api_helpers import get_preview_url_from_node


class PreviewLookupTestCase(TestCase):
    @patch('api_helpers.subprocess.run')
    def test_successful_preview(self, run):
        run.return_value.stdout = '{"previewUrls": ["https://example.com/audio.mp3"]}'
        self.assertEqual(get_preview_url_from_node('Song Artist'), 'https://example.com/audio.mp3')

    @patch('api_helpers.subprocess.run')
    def test_library_failure_is_logged(self, run):
        run.return_value.stdout = '{"previewUrls": [], "error": "Missing credentials"}'
        with self.assertLogs('api_helpers', level='WARNING') as logs:
            self.assertIsNone(get_preview_url_from_node('Song Artist'))
        self.assertIn('Missing credentials', logs.output[0])

    @patch('api_helpers.subprocess.run')
    def test_node_dependency_failure_is_logged(self, run):
        run.side_effect = subprocess.CalledProcessError(
            1, ['node'], stderr='Cannot find module spotify-preview-finder')
        with self.assertLogs('api_helpers', level='WARNING') as logs:
            self.assertIsNone(get_preview_url_from_node('Song Artist'))
        self.assertIn('Cannot find module', logs.output[0])

    @patch('api_helpers.subprocess.run')
    def test_timeout_returns_no_preview(self, run):
        run.side_effect = subprocess.TimeoutExpired(['node'], 20)
        with self.assertLogs('api_helpers', level='WARNING'):
            self.assertIsNone(get_preview_url_from_node('Song Artist'))
