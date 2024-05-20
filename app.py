import streamlit as st
import pandas as pd
from spotify_utils import get_audio_features, play_track
from llm import get_llm_recommendations
import spotipy

# Set Streamlit page configuration
st.set_page_config(
    page_title="AutoSpotify",
    page_icon="🎵",
    layout="centered",
    initial_sidebar_state="auto"
)

# Function to fetch and store audio features of the last 10 saved tracks
def fetch_audio_features():
    if 'tracks' not in st.session_state:
        df, tracks = get_audio_features(limit=10)
        st.session_state.tracks = tracks

# Function to fetch and store recommendations based on user input using LLM
def fetch_recommendations(user_input):
    if 'last_user_input' not in st.session_state or st.session_state.last_user_input != user_input:
        st.session_state.last_user_input = user_input
        rec_tracks,function_calls_df = get_llm_recommendations(user_input)
        try :
            track_names, artist_names, track_ids = zip(*rec_tracks)
        except:
            print(rec_tracks)
        st.session_state.llm_rec_track_names = list(track_names)
        st.session_state.llm_rec_artist_names = list(artist_names)
        st.session_state.llm_rec_track_ids = list(track_ids)
        st.session_state.function_calls_df = function_calls_df

# Function to display recommendations
def display_recommendations():
    if 'llm_rec_track_names' in st.session_state:
        recommendations = pd.DataFrame(
            {
                'Track': st.session_state.llm_rec_track_names,
                'Artist': st.session_state.llm_rec_artist_names
            }
        )
        st.subheader('Recommendations based on your input:')
        st.dataframe(recommendations)

# Function to handle track selection and playback
def handle_track_selection():
    if 'llm_rec_track_names' in st.session_state:
        selected_track_name = st.selectbox(
            'Select a track to play',
            options=[f'{name} by {artist}' for name, artist in zip(st.session_state.llm_rec_track_names, st.session_state.llm_rec_artist_names)]
        )

        if selected_track_name:
            selected_index = next(
                (i for i, (name, artist) in enumerate(zip(st.session_state.llm_rec_track_names, st.session_state.llm_rec_artist_names))
                 if f'{name} by {artist}' == selected_track_name), None)

            if selected_index is not None:
                selected_track = st.session_state.llm_rec_track_names[selected_index]
                selected_artist = st.session_state.llm_rec_artist_names[selected_index]
                track_id = st.session_state.llm_rec_track_ids[selected_index]
                track_uri = f'spotify:track:{track_id}'

                if st.button('Play Selected Track'):
                    st.write(f'Playing {selected_track} by {selected_artist}')
                    try:
                        play_track(track_uri)
                        st.success(f'Playing {selected_track} by {selected_artist}')
                    except Exception as e:
                        st.error(f'Error playing track: {e}')
            else:
                st.error('No track selected.')

# Run the app
if __name__ == "__main__":
    auth_manager = spotipy.oauth2.SpotifyOAuth(show_dialog=True)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    st.title('Spotify Audio Features')

    user_input = st.text_input("Enter your request for recommendations:")
    if user_input:
        fetch_recommendations(user_input)
        display_recommendations()
        handle_track_selection()

        st.dataframe(st.session_state.function_calls_df)
    
    
