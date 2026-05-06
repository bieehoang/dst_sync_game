
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from src.logger import logger
import yaml
import os

_sp = None  # private, dùng getter thay vì import trực tiếp

def _load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config.yaml"
    )
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def init_spotify():
    global _sp
    try:
        cfg = _load_config().get("spotify", {})
        auth_manager = SpotifyOAuth(
            client_id=cfg["client_id"],
            client_secret=cfg["client_secret"],
            redirect_uri=cfg.get("redirect_uri", "http://127.0.0.1:8888/callback"),
            scope="playlist-read-private playlist-read-collaborative",
            cache_path=".spotify_cache",
            show_dialog=False,
            open_browser=False
        )
        _sp = spotipy.Spotify(auth_manager=auth_manager)
        user = _sp.current_user()
        logger.info(f"Spotify OK: {user.get('display_name', 'Unknown')}")
        return True
    except Exception as e:
        logger.error(f"Spotify init failed: {e}")
        _sp = None
        return False

def get_spotify_client():
    """Dùng cái này thay vì import sp trực tiếp"""
    global _sp
    if _sp is None:
        init_spotify()
    return _sp  # có thể vẫn None nếu init fail, caller tự check

# Init khi import
init_spotify()