import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from src.logger import logger   # Dùng logger chung của bot
import yaml, os

def load_spotify_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config.get("spotify", {})

def init_spotify():
    global sp
    try:
        auth_manager = SpotifyOAuth(
            client_id=cfg["client_id"],
            client_secret=cfg["client_secret"],
            redirect_uri=cfg["redirect_uri"],
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
