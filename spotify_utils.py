import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

scope = 'user-library-read user-modify-playback-state streaming'
auth_manager = SpotifyOAuth(scope=scope)
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_audio_features(limit=10):
    results = sp.current_user_saved_tracks(limit=limit)
    tracks = results['items']
    track_ids = [track['track']['id'] for track in tracks]
    audio_features = sp.audio_features(track_ids)

    df = pd.DataFrame(audio_features)
    df['track_name'] = [track['track']['name'] for track in tracks]
    df['track_id'] = [track['track']['id'] for track in tracks]
    df.set_index('track_name', inplace=True)
    return df, tracks

def get_recommendations(track_id):
    recommendations = sp.recommendations(seed_tracks=[track_id])
    rec_tracks = recommendations['tracks']
    rec_track_names = [track['name'] for track in rec_tracks]
    rec_artist_names = [track['artists'][0]['name'] for track in rec_tracks]
    return rec_tracks, rec_track_names, rec_artist_names

def play_track(uri):
    sp.start_playback(uris=[uri])

def get_genre_seeds():
    return sp.recommendation_genre_seeds()['genres']

def get_artist_id(artist_name):
    results = sp.search(q=f'artist:{artist_name}', type='artist')
    return results['artists']['items'][0]['id']

def get_track_id(track_name, artist_name=None):
    if artist_name:
        results = sp.search(q=f'track:{track_name} artist:{artist_name}', type='track')
    else:
        results = sp.search(q=f'track:{track_name}', type='track')
    return results['tracks']['items'][0]['id']
