import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID = "b82cf42b203b4c6d98f8531d87cf5a7f"
CLIENT_SECRET = "d8891f6a380b4785b3607f21d458243e"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

sp = None   # sẽ khởi tạo sau

def init_spotify():
    global sp
    
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="playlist-read-private playlist-read-collaborative",
        cache_path=".spotify_cache",
        show_dialog=True
    )

    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Test authentication
    try:
        user = sp.current_user()
        print(f"✅ Spotify OAuth thành công! Đăng nhập với tài khoản: {user.get('display_name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Spotify OAuth chưa sẵn sàng: {e}")
        auth_url = auth_manager.get_authorize_url()
        print(f"\n🔗 Vui lòng mở link sau để đăng nhập Spotify:")
        print(f"{auth_url}\n")
        return False


# Khởi tạo khi import
if sp is None:
    init_spotify()
