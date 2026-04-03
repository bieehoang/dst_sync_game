import yt_dlp
import random
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
    "cookies": "/home/steam/dst-discord-chat-sync/cookies.txt",   # ← Đường dẫn cookies
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
def get_related(query: str):
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)

        candidates = info["entries"][1:]  # bỏ bài đầu

        if not candidates:
            return None

        entry = random.choice(candidates)  # 🔥 random

        return {
            "url": entry["url"],
            "title": entry["title"]
        }
