import discord
from src.music.ytdl import get_audio_url, get_related
from src.music.queue import MusicQueue
import asyncio
from src.logger import logger
import aiohttp

queues = {}  # guild_id -> queue


def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = MusicQueue()
    return queues[guild_id]


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
    track = q.next()                     # Lấy bài tiếp theo trong queue

    # Nếu queue hết nhưng autoplay đang bật → tự tìm bài related
    if not track and q.autoplay:
        if q.history:
            last_track = q.history[-1]
            related = get_related(last_track["title"])
            
            if related:
                # Tránh lặp lại bài vừa phát
                if related["title"] not in [t["title"] for t in q.history[-5:]]:
                    track = related
                    q.history.append(track)
                    logger.info(f"[AUTOPLAY] Added related song: {track['title']}")
                else:
                    logger.info("[AUTOPLAY] Related song already played recently, skipping...")
            else:
                logger.info("[AUTOPLAY] No related song found")
        else:
            logger.info("[AUTOPLAY] No history to get related song")

    if not track:
        await message.channel.send("404 not found")
        await set_voice_status(bot, vc.channel.id, "")
        return

    await set_voice_status(bot, vc.channel.id, f"Listening: {track['title'][:50]}")

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            track["url"],
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        ),
        volume=q.volume
    )

    def after(_):
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

    # Connect voice nếu chưa có
    if not message.guild.voice_client:
        vc = await channel.connect()
    else:
        vc = message.guild.voice_client

    if "spotify.com" in query:
        query = get_spotify_track(query)

    data = await asyncio.to_thread(get_audio_url, query)
    if not data:
        await message.channel.send("404")
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

    # ================== QUAN TRỌNG: BẮT ĐẦU PHÁT NHẠC ==================
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
            if resp.status != 200:
                logger.warning(f"Voice status error: {resp.status}")
