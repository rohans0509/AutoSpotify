from spotify_utils import get_track_id, get_artist_id, get_genre_seeds
import google.generativeai as genai
from langchain_core.tools import tool
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import random
from typing import List,Dict

load_dotenv()


auth_manager = SpotifyOAuth()
sp = spotipy.Spotify(auth_manager=auth_manager)

def recommendations(
    artist_names: List[str] = [],
    track_names: List[str] = [],
    genre_names: List[str] = [],
    limit: int = 5,
    **kwargs
):
    if isinstance(artist_names, str):
        artist_names = [artist_names]
    if isinstance(track_names, str):
        track_names = [track_names]
    if isinstance(genre_names, str):
        genre_names = [genre_names]

    total_length = len(artist_names) + len(track_names) + len(genre_names)
    if total_length > 5:
        num_artists = random.randint(0, len(artist_names))
        num_tracks = random.randint(0, min(len(track_names), 5 - num_artists))
        num_genres = 5 - num_artists - num_tracks

        artist_names = random.sample(artist_names, num_artists)
        track_names = random.sample(track_names, num_tracks)
        genre_names = random.sample(genre_names, num_genres)
    
    artist_ids = [get_artist_id(artist) for artist in artist_names]
    track_ids = [get_track_id(track) for track in track_names]

    rec_tracks = sp.recommendations(seed_artists=artist_ids, seed_tracks=track_ids, seed_genres=genre_names, limit=int(limit), **kwargs)
    rec_tracks = [(track['name'],track['artists'][0]['name'], track['id']) for track in rec_tracks['tracks']]
    # rec_tracks = dict(rec_tracks)
    print(len(rec_tracks))

    return rec_tracks

def available_genre_seeds():
    return get_genre_seeds()

def get_llm_recommendations(user_input: str) -> Dict[str, str]:
    model = genai.GenerativeModel(model_name='gemini-1.0-pro', tools=[recommendations])
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(user_input)
    for content in chat.history:
        part = content.parts[0]
        print(content.role, "->", type(part).to_dict(part))
        print('-'*80)
    for content in chat.history:
        part = content.parts[0]
        out=type(part).to_dict(part)
        try :
            if out["function_response"]["name"]=="recommendations":
                return out["function_response"]["response"]["result"]
            
        except:
            pass

    return {}

