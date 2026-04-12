import discord
from src.music.ytdl import get_audio_url, get_related, get_spotify_track
from src.music.queue import MusicQueue
import asyncio
from src.logger import logger
import aiohttp
import os
import yt_dlp
from src.music.ytdl import YTDL_OPTIONS
TEMP_DIR = "/tmp/dst_music"
os.makedirs(TEMP_DIR, exist_ok=True)

queues = {}  # guild_id -> queue


def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = MusicQueue()
    return queues[guild_id]

async def refresh_audio_url(webpage_url: str):
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = await asyncio.to_thread(
                ydl.extract_info, webpage_url, False
            )

            if not info:
                return None

            formats = info.get("formats", [])

            audio = max(
                (f for f in formats if f.get("acodec") != "none"),
                key=lambda f: f.get("abr") or 0,
                default=None
            ) 

            return audio.get("url") if audio else None  # ✅ FIX

    except Exception as e:
        logger.error(f"[Refresh URL] Error: {e}")
        return None

async def preload_next_track(q: MusicQueue):
    next_track = q.peek()
    if not next_track or "webpage_url" not in next_track:
        return

    try:
        await refresh_audio_url(next_track["webpage_url"])
        logger.info(f"[PRELOAD] Đã refresh sẵn: {next_track['title']}")
    except:
        pass

async def ensure_voice(message):
    if not message.author.voice:
        await message.channel.send("Join voice first bro!")
        return None
    channel = message.author.voice.channel
    if message.guild.voice_client and message.guild.voice_client.channel != channel:
        await message.channel.send("Vo chung voi tau!")
        return None
    return channel


async def play_next(bot, vc, message):
    q = get_queue(message.guild.id)
    track = q.next()                     

    if not track and q.autoplay:
        if q.history:
            last_track = q.history[-1]
            related = get_related(
                    last_track.get("title", ""),
                    last_track.get("webpage_url"),
                    history=q.history
                    )
                        
            if related:
                # Tránh lặp lại bài vừa phát
                if related["title"] not in [t["title"] for t in q.history[-5:]]:
                    q.add(related) 
                    track = q.next()
                    logger.info(f"[AUTOPLAY] Added related song: {track['title']}")
                else:
                    logger.info("[AUTOPLAY] Related song already played recently, retry...")
                    related = get_related(
                    last_track.get("title", ""),
                    last_track.get("webpage_url"),
                    history=q.history
                    ) 
            else:
                logger.info("[AUTOPLAY] No related song found")
        else:
            logger.info("[AUTOPLAY] No history to get related song")

    if not track:
        await message.channel.send("503")
        await set_voice_status(bot, vc.channel.id, "")
        return

    await set_voice_status(bot, vc.channel.id, f"Listening: {track['title'][:50]}")
    
    audio_url = await refresh_audio_url(track["webpage_url"])
    if not audio_url:
        await message.channel.send(f"503: {track['title']}")
        logger.info(f"[DEBUG] webpage_url: {track.get('webpage_url')}")
        logger.info(f"[DEBUG] audio_url: {audio_url}")
        return await play_next(bot, vc, message)  # thử bài tiếp theo

    asyncio.create_task(preload_next_track(q))
    
    source = discord.FFmpegOpusAudio(
            audio_url,
            before_options=(
            "-reconnect 0.1 "
            "-reconnect_streamed 0.1 "
            "-reconnect_delay_max 0.1 "
            "-reconnect_on_network_error 0.1 "
            "-reconnect_on_http_error 4xx,5xx "
            ),
            options="-vn -buffer_size 256k" 
    )

    def after(error):
        q.history.append(track)
        if error:
            logger.error(f"Playback error: {error}")
        asyncio.run_coroutine_threadsafe(play_next(bot, vc, message), vc.loop)
    
    vc.play(source, after=after)

    embed = discord.Embed(
        title="Now Playing",
        description=track["title"],
        color=0x00ffcc
    )
    await message.channel.send(embed=embed)

async def play_music(bot, message, query: str):
    channel = await ensure_voice(message)
    if not channel:
        return

    if not message.guild.voice_client:
        vc = await channel.connect()
    else:
        vc = message.guild.voice_client

    original_query = query
    if "spotify.com" in query:
        data = get_spotify_track(query)
        if not data:
            await message.channel.send("Wyvern - 503 Spotify")
            return
    else:
        data = await asyncio.to_thread(get_audio_url, query) 
    if not data:
        await message.channel.send("501")
        return

    q = get_queue(message.guild.id)

    if isinstance(data, list):           # Playlist
        for track in data:
            q.add(track)
        await message.channel.send(f"Added playlist **{len(data)}** songs")
    else:                                # Single track
        q.add(data)
        embed = discord.Embed(
            title="Added to Queue",
            description=f"**{data['title']}**",
            color=0x3498db
        )
        await message.channel.send(embed=embed)

    if not vc.is_playing() and not vc.is_paused():
        await play_next(bot, vc, message)

async def set_voice_status(bot, channel_id: int, text: str):
    url = f"https://discord.com/api/v10/channels/{channel_id}/voice-status"
    headers = {
        "Authorization": f"Bot {bot.http.token}",
        "Content-Type": "application/json"
    }
    payload = {"status": text}
    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=payload, headers=headers) as resp:
            if resp.status not in (200, 204):
                logger.warning(f"Voice status error: {resp.status}")
