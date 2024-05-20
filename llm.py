from spotify_utils import get_track_id, get_artist_id, get_genre_seeds
import google.generativeai as genai
from langchain_core.tools import tool
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import random
from typing import List,Dict
import pandas as pd

load_dotenv()


auth_manager = SpotifyOAuth()
sp = spotipy.Spotify(auth_manager=auth_manager)


# Use schema with : notation
def recommendations(
    artist_names: List[str] = [],
    track_names: List[str] = [],
    genre_names: List[str] = [],
    limit: int = 20,
    **kwargs
):
    """ Get a list of recommended tracks for one to five seeds.

        Parameters:
            - artist_names: a list of artist names
            - track_names: a list of track names
            - genre_names: a list of genre names. Available genres for
                            recommendations can be found by calling
                            available_genre_seeds()

            - limit: The maximum number of items to return. Default: 20.
                     Minimum: 1. Maximum: 100

            - min/max/target_<attribute>: For the tunable track
                attributes listed below, these values provide filters
                and targeting on results. Use these in kwargs
                
                Available tuneable track attributes:
                    - valence: Measures Happiness [0, 1]
                    - acousticness: [0, 1]
                    - danceability: [0, 1]
                    - duration_ms: [0, +∞)
                    - energy: [0, 1]
                    - instrumentalness: [0, 1]
                    - key: [0, 11]
                    - liveness: [0, 1]
                    - loudness: [-60, 0]
                    - mode: [0, 1]
                    - popularity: [0, 100]
                    - speechiness: [0, 1]
                    - tempo: [0, +∞)
                    - time_signature: [0, 11]

                For example, you can specify the following parameters
                to get recommendations for tracks that are in the key of
                C major and have minimum valence of 0.8 (happiness):
                    - key=0
                    - min_valence=0.8

                Or you can specify the following parameters to get
                recommendations for tracks that are in the key of D major
                and have target tempo of 90:
                    - key=2
                    - target_tempo=90

        Returns:
            - rec_tracks: a dictionary of recommended tracks with the
                {track_name: artist_name} format

        Example:
            recommendations(artist_names=['Kygo'],
                            track_names=['Stargazing'],
                            genre_names=['pop'],
                            limit=10)
    """
    print(artist_names, track_names, genre_names, limit)
    # convert to list if str
    if isinstance(artist_names, str):
        artist_names = [artist_names]
    if isinstance(track_names, str):
        track_names = [track_names]
    if isinstance(genre_names, str):
        genre_names = [genre_names]


    total_length=len(artist_names)+len(track_names)+len(genre_names)
    if total_length >5:
        num_artists=random.randint(0,len(artist_names))
        num_tracks=random.randint(0,min(len(track_names),5-num_artists))
        num_genres=5-num_artists-num_tracks

        artist_names=random.sample(artist_names,num_artists)
        track_names=random.sample(track_names,num_tracks)
        genre_names=random.sample(genre_names,num_genres)
    
    artist_ids=[get_artist_id(artist) for artist in artist_names]
    track_ids=[get_track_id(track) for track in track_names]

    rec_tracks = sp.recommendations(seed_artists=artist_ids, seed_tracks=track_ids, seed_genres=genre_names, limit=int(limit), **kwargs)
    rec_tracks = [(track['name'],track['artists'][0]['name'], track['id']) for track in rec_tracks['tracks']]
    return rec_tracks

def available_genre_seeds():
    """ Get a list of available genre seeds for recommendations.

        Returns:
            - genre_seeds: a list of available genre seeds

        Example:
            available_genre_seeds()
    """
    genre_seeds = get_genre_seeds()
    return genre_seeds


def extract_function_calls_and_responses(chat_history):
    function_data = []
    
    # Extract function calls and responses
    for content in chat_history:
        part = content.parts[0]
        out = type(part).to_dict(part)
        
        if "function_call" in out:
            function_data.append({
                "type": "function_call",
                "name": out["function_call"]["name"],
                "response": out["function_call"]["args"]
            })
        
        if "function_response" in out:
            function_data.append({
                "type": "function_response",
                "name": out["function_response"]["name"],
                "response": out["function_response"]["response"]
            })
    
    # Convert to DataFrame for better readability
    function_df = pd.DataFrame(function_data)
    
    return function_df

def get_llm_recommendations(user_input: str) -> Dict[str, str]:
    context="Use available_genre_seeds to get list of genres if you need them. Use the kwargs in recommendations if you need them.\n"
    model = genai.GenerativeModel(model_name='gemini-1.0-pro', tools=[recommendations, available_genre_seeds])
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(context+user_input)
    for content in chat.history:
        part = content.parts[0]
        out=type(part).to_dict(part)
        if "function_call" in out.keys():
            print('-'*80)
            print("Function call")
            print(out["function_call"])
            print('-'*80)
 
    function_calls_df = extract_function_calls_and_responses(chat.history)

    
    # Extract recommendations from function responses
    recommendations_result = {}
    for _, row in function_calls_df.iterrows():

        if row["type"]=="function_response" and row["name"]=="recommendations":
            recommendations_result = row["response"]["result"]
            break

    return recommendations_result, function_calls_df

