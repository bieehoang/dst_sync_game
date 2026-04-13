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
    "cookies": "/home/steam/dst-discord-chat-sync/cookies.txt",
    "http_headers": {
        "User-Agent": "Mozilla/5.0"
    },
    "geo_bypass": True,
    "age_limit": 0,

    "js_runtimes":{ 
        "deno":{
            "path": "/home/steam/.deno/bin/deno"
            }
        },
    "remote_components": ["ejs:github"],

    "extractor_args": {
        "youtube": {
            "player_client": ["web"]
        }
    }
}

def get_audio_url(query):
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        try:
            if "youtube.com" in query or "youtu.be" in query:
                info = ydl.extract_info(query, download=False)

                if not info:
                    return None

                if "entries" in info:
                    results = []
                    for entry in info["entries"]:
                        if not entry:
                            continue
                        results.append({
                            "title": entry.get("title") or "Unknown Title",
                            "webpage_url": entry.get("webpage_url")
                        })
                    return results if results else None

                return {
                    "title": info.get("title") or "Unknown Title",
                    "webpage_url": info.get("webpage_url")
                    }

            # ================= SEARCH =================
            search_query = f"ytsearch5:{query}"
            info = ydl.extract_info(search_query, download=False)

            candidates = info.get("entries", []) if info else []

            if not candidates:
                logger.warning(f"[YTDL] No results for: {query}")
                return None

            best = None
            best_score = 0
            query_lower = query.lower() 
            artist = query_lower.split("-")[0].strip() if "-" in query_lower else ""
            for v in candidates:
                if not v:
                    continue

                title = (v.get("title") or "").lower()
                views = v.get("view_count") or 0
                duration = v.get("duration") or 0

                score = views

                if 120 <= duration <= 420:
                    score *= 1.5
                if query_lower in title:
                    score *= 3
                if "official" in title:
                    score *= 2
                if artist and artist in title:
                    score *= 2 
                if score > best_score:
                    best = v
                    best_score = score

            # fallback an toàn
            if not best:
                best = candidates[0]

            if not best:
                return None

            return {
                "title": best["title"],
                "webpage_url": best.get("webpage_url")
                }

        except Exception as e:
            logger.error(f"get_audio_url error: {e}")
            return None

def get_related(last_track_title: str, last_track_url: str = None, history=None):
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

            if artist and len(artist) > 3:
                search_query = f"ytsearch10:{artist} {clean_title}"
                info = ydl.extract_info(search_query, download=False)
                candidates = info.get("entries", [])

                for v in candidates:
                    if not v or not v.get("title"):
                        continue
                    
                    title_lower = v["title"].lower()
                    
                    if clean_title in title_lower and artist and artist.lower() in title_lower:
                        continue
                    duration = v.get("duration") or 0
                    if 150 <= duration <= 360:          # 2.5 - 6 phút
                        return {
                            "url": v["url"],
                            "title": v["title"]
                        }

            search_query = f"ytsearch10:{clean_title} official audio"
            info = ydl.extract_info(search_query, download=False)
            candidates = info.get("entries", [])

            if not candidates:
                return None
            import random
            random.shuffle(candidates)
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
                # ❌ tránh lặp bài
                if history and title in [t["title"].lower() for t in history[-10:]]: 
                    continue
                # ❌ hạn chế lặp artist
                uploader = (v.get("uploader") or "").lower()
                if artist and artist.lower() in uploader:
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
                    "title": best["title"],
                    "webpage_url": best.get("webpage_url")
                        }

            # Fallback: lấy bài thứ 2
            if len(candidates):
                return {
                    "title": v["title"], 
                    "webpage_url": v.get("webpage_url")
                        }

            return None

        except Exception as e:
            logger.error(f"get_related error: {e}")
            return None
def get_spotify_track(spotify_url: str):
    """Convert Spotify URL → YouTube audio (track | playlist | album)"""
    try:
        from src.music.spotify import sp

        if not sp:
            logger.error("Spotify client not initialized")
            return None

        # ================= TRACK =================
        if "track/" in spotify_url:
            track_id = spotify_url.split("track/")[-1].split("?")[0]
            track = sp.track(track_id)

            name = track['name']
            artist = track['artists'][0]['name']

            logger.info(f"[Spotify TRACK] {artist} - {name}")

            return get_audio_url(f"{name} {artist} official audio")

        # ================= PLAYLIST =================
        elif "playlist/" in spotify_url:
            playlist_id = spotify_url.split("playlist/")[-1].split("?")[0]

            results = sp.playlist_items(playlist_id)
            tracks = []

            for item in results['items']:
                t = item.get('track')
                if not t:
                    continue

                name = t['name']
                artist = t['artists'][0]['name']

                query = f"{name} {artist} official audio"
                yt_data = get_audio_url(query)

                if yt_data:
                    tracks.append(yt_data)

            logger.info(f"[Spotify PLAYLIST] Loaded {len(tracks)} tracks")

            return tracks

        # ================= ALBUM =================
        elif "album/" in spotify_url:
            album_id = spotify_url.split("album/")[-1].split("?")[0]

            results = sp.album_tracks(album_id)
            tracks = []

            for t in results['items']:
                name = t['name']
                artist = t['artists'][0]['name']

                query = f"{name} {artist} official audio"
                yt_data = get_audio_url(query)

                if yt_data:
                    tracks.append(yt_data)

            logger.info(f"[Spotify ALBUM] Loaded {len(tracks)} tracks")

            return tracks

        else:
            logger.warning(f"Unsupported Spotify URL: {spotify_url}")
            return None

    except Exception as e:
        logger.error(f"Spotify conversion error: {e}")
        return None
