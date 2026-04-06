import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from src.logger import logger   # Dùng logger chung của bot

CLIENT_ID = "b82cf42b203b4c6d98f8531d87cf5a7f"
CLIENT_SECRET = "d8891f6a380b4785b3607f21d458243e"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

sp = None

def init_spotify():
    global sp
    try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="playlist-read-private playlist-read-collaborative",
            cache_path=".spotify_cache",
            show_dialog=False,          # Không hiện popup trên server
            open_browser=False
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        user = sp.current_user()
        print(f"✅ Spotify OAuth thành công! Logged in as: {user.get('display_name', 'Unknown')}")
        logger.info("Spotify client initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Spotify OAuth failed: {e}")
        print(f"❌ Spotify OAuth failed: {e}")
        return False


# Khởi tạo khi import
if sp is None:
    init_spotify()
