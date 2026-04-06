import yt_dlp
import random
from src.logger import logger
class NoLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no-warnings": True,
    "noplaylist": True,
    "logger":NoLogger(),
    "extract flat": False,
    "cookiefile": "/home/steam/dst-discord-chat-sync/cookies.txt", 
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    },
    "geo_bypass": True,
    "age_limit": 0,
}

def get_audio_url(query):
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        if "youtube.com" in query or "youtu.be" in query:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                results = []
                for entry in info["entries"]:
                    if not entry:
                        continue
                    results.append({
                        "url": entry["url"],
                        "title": entry["title"]
                    })
                return results  # ⚠️ list

            return {
                "url": info["url"],
                "title": info["title"]
            }

        # 🎯 search thông minh
        search_query = f"ytsearch5:{query} official audio"

        info = ydl.extract_info(search_query, download=False)
        candidates = info["entries"]

        best = None
        best_score = 0

        for v in candidates:
            title = v.get("title", "").lower()
            views = v.get("view_count") or 0
            duration = v.get("duration") or 0

            # ❌ filter rác
            if any(x in title for x in ["live", "remix", "cover", "8d"]):
                continue

            score = views

            # 🎯 ưu tiên độ dài chuẩn
            if 120 <= duration <= 420:
                score *= 1.5

            # 🎯 ưu tiên official
            if "official" in title:
                score *= 2

            if score > best_score:
                best = v
                best_score = score

        if not best:
            best = candidates[0]

        return {
            "url": best["url"],
            "title": best["title"]
        }
def get_related(last_track_title: str, last_track_url: str = None):
    """
    Tìm bài hát related thông minh:
    - Ưu tiên 1: Cùng ca sĩ, bài khác
    - Ưu tiên 2: Cùng thể loại / vibe (tạo làn gió mới)
    """
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        try:
            artist = None

            # Lấy thông tin nghệ sĩ từ URL nếu có
            if last_track_url and ("youtube.com" in last_track_url or "youtu.be" in last_track_url):
                try:
                    info = ydl.extract_info(last_track_url, download=False, ignore_errors=True)
                    if info:
                        artist = info.get("artist") or info.get("uploader") or info.get("channel")
                except:
                    pass

            # Làm sạch tiêu đề
            clean_title = last_track_title.lower()
            for word in ["official", "audio", "lyrics", "remix", "cover", "live", "version", "ft.", "feat", "music video"]:
                clean_title = clean_title.replace(word, "").strip()

            # ================== ƯU TIÊN 1: CÙNG CA SĨ - BÀI KHÁC ==================
            if artist and len(artist) > 3:
                search_query = f"ytsearch10:{artist} -\"{clean_title}\""
                info = ydl.extract_info(search_query, download=False)
                candidates = info.get("entries", [])

                for v in candidates:
                    if not v or not v.get("title"):
                        continue
                    
                    title_lower = v["title"].lower()
                    
                    # Bỏ qua bài đang nghe và các bản rác
                    if clean_title in title_lower or any(x in title_lower for x in ["remix", "cover", "live", "8d", "slowed", "reverb"]):
                        continue

                    duration = v.get("duration") or 0
                    if 150 <= duration <= 360:          # 2.5 - 6 phút
                        return {
                            "url": v["url"],
                            "title": v["title"]
                        }

            # ================== ƯU TIÊN 2: CÙNG THỂ LOẠI / VIBE ==================
            search_query = f"ytsearch8:{clean_title} similar OR like OR vibe OR playlist OR mix"

            info = ydl.extract_info(search_query, download=False)
            candidates = info.get("entries", [])

            if not candidates:
                return None

            best = None
            best_score = -1

            for v in candidates:
                if not v or not v.get("title"):
                    continue

                title = v["title"].lower()
                views = v.get("view_count") or 0
                duration = v.get("duration") or 0

                # Lọc rác mạnh
                if any(bad in title for bad in ["live", "cover", "remix", "8d", "slowed", "reverb", "lyrics video", "1 hour", "extended"]):
                    continue

                score = views

                # Ưu tiên độ dài chuẩn (2.5 - 5.5 phút)
                if 150 <= duration <= 330:
                    score *= 2.5

                # Ưu tiên có từ khóa vibe / similar / playlist
                if any(word in title for word in ["similar", "like", "vibe", "playlist", "mix", "chill"]):
                    score *= 1.8

                if score > best_score:
                    best_score = score
                    best = v

            if best:
                return {
                    "url": best["url"],
                    "title": best["title"]
                }

            # Fallback: lấy bài thứ 2
            if len(candidates) >= 2:
                return {
                    "url": candidates[1]["url"],
                    "title": candidates[1]["title"]
                }

            return None

        except Exception as e:
            logger.error(f"get_related error: {e}")
            return None

def get_spotify_track(spotify_url: str):
    """Convert Spotify URL sang YouTube search query"""
    try:
        # Import sp ở đây để tránh lỗi circular import
        from src.music.spotify import sp

        if not sp:
            logger.error("Spotify client not initialized")
            return None

        # Lấy track ID từ URL
        if "track/" in spotify_url:
            track_id = spotify_url.split("track/")[-1].split("?")[0]
        else:
            logger.warning(f"Invalid Spotify URL: {spotify_url}")
            return None

        track = sp.track(track_id)

        track_name = track['name']
        artist_name = track['artists'][0]['name']

        # Tạo query tìm kiếm tốt trên YouTube
        search_query = f"{track_name} {artist_name} official audio"

        logger.info(f"[Spotify → YouTube] {artist_name} - {track_name}")

        # Gọi get_audio_url để tìm bài trên YouTube
        return get_audio_url(search_query)

    except Exception as e:
        logger.error(f"Spotify conversion error: {e}")
        # Fallback: search đơn giản
        try:
            simple_name = spotify_url.split("/")[-1].replace("-", " ").replace("?", "")
            return get_audio_url(simple_name)
        except:
            return None
