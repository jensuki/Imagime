import requests
import mimetypes
from utils.secret import EPIX_CLIENT_ID, EPIX_API_KEY, SPOT_CLIENT_ID, SPOT_API_KEY
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# setup spotipy credentials
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOT_CLIENT_ID, client_secret=SPOT_API_KEY))

def extract_keywords_only(response):
    """Extract keyword text values from JSON repsonse"""

    if response.get('status') == 'ok':
        keywords = response.get('keywords', [])
        return [k.get('keyword') for k in keywords]
    return None

def image_to_keywords(image_url=None, local_image_file=None, num_keywords=10):
    """Analyze image to extract keywords"""

    BASE_URL = 'https://api.everypixel.com/v1/keywords'
    AUTH = (EPIX_CLIENT_ID, EPIX_API_KEY)
    params = {'num_keywords': num_keywords}

    if image_url:
        # handle get request for image url
        params['url'] = image_url
        response = requests.get(BASE_URL, params=params, auth=AUTH)

    elif local_image_file:
        # handle post request for uploaded image file
        mime_type = mimetypes.guess_type(local_image_file)[0]
        with open(local_image_file, 'rb') as file:
            files = {'data': ('image', file, mime_type)}
            response = requests.post(BASE_URL, files=files, auth=AUTH)
    else:
        raise ValueError('You must provide a valid image URL or image file.')

    if response.status_code == 200:
        return extract_keywords_only(response.json())
    else:
        response.raise_for_status()

def keywords_to_songs(keywords, limit=5):
    """Map keywords to songs"""

    songs = []
    seen_combos = set() # to store unique (title, artist) combos

    for keyword in keywords:
        result = sp.search(q=keyword, type='track', limit=limit)

        for track in result['tracks']['items']:
            title = track['name']
            artist = track['artists'][0]['name']
            combos = (title, artist) # create tuple of title and artist

            # only add songs with previews + unique title-artist combos to avoid dupes
            if track.get('preview_url') and combos not in seen_combos:
                song_details = {
                    'title': title,
                    'artist': artist,
                    'album': track['album']['name'],
                    'image_url': track['album']['images'][0]['url'],
                    'spotify_url': track['external_urls']['spotify'],
                    'preview_url': track['preview_url']
                }

                songs.append(song_details)
                seen_combos.add(combos) # mark this combo as seen

    return songs
