import wavelink
from src.logger import logger

async def play_music(bot, message, search: str):
    if not message.author.voice or not message.author.voice.channel:
        await message.channel.send("Join voice truoc!")
        return

    voice_channel = message.author.voice.channel

    try:
        # NEW correct way for wavelink 3.x + Lavalink v4
        if not message.guild.voice_client:
            player: wavelink.Player = await wavelink.Player.connect(
                channel=voice_channel,
                self_deaf=True
            )
        else:
            player: wavelink.Player = message.guild.voice_client

        # search + play
        tracks = await wavelink.Playable.search(search)
        if not tracks:
            await message.channel.send("ko bik bai nay!")
            return

        track = tracks[0]
        await player.play(track)
        await message.channel.send(f"**Playing:** {track.title} by {track.author}")

        logger.info(f"Started playing: {track.title} | Guild: {message.guild.name}")

    except Exception as e:
        logger.error(f"Music crash: {e}")
        print(f"Music crash: {e}")
        await message.channel.send(f"<@1005125632176443492>: {str(e)[:150]} (check console)")
