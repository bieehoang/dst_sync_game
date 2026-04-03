from src.music.player import play_music, get_queue
import discord
import random

async def handle_music(bot, message):
    content = message.content.strip()

    if content.startswith("!play") or content.startswith("!p"):
        query = content.split(" ", 1)
        if len(query) < 2:
            await message.channel.send("Bai j!")
            return True
        query = query[1].strip()  # 🔥 CHỈ LẤY PHẦN SAU COMMAND
        await play_music(bot, message, query)
        return True
    if content == "!skip":
        vc = message.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
        return True

    if content == "!stop":
        vc = message.guild.voice_client
        if vc:
            await vc.disconnect()
        return True

    if content == "!queue":
        q = get_queue(message.guild.id)
        if not q.queue:
            return await message.channel.send("ko co queue!")

        text = "\n".join([f"{i+1}. {t['title']}" for i, t in enumerate(q.queue)])
        await message.channel.send(f"Queue:\n{text}")
        return True

    if content == "!loop":
        q = get_queue(message.guild.id)
        q.loop = not q.loop
        await message.channel.send(f"Loop: {q.loop}")
        return True

    if content == "!back":
        q = get_queue(message.guild.id)
        track = q.back()
        if track:
            vc = message.guild.voice_client
            vc.stop()
        else:
            await message.channel.send("ko bik!")
        return True

    if content.startswith("!volume"):
        try:
            vol = int(content.split()[1]) / 100
            q = get_queue(message.guild.id)
            q.volume = vol

            vc = message.guild.voice_client
            if vc and vc.source:
                vc.source.volume = vol

            await message.channel.send(f"Volume: {int(vol*100)}%")
        except:
            await message.channel.send("Set: !volume 0-100")
        return True
    if content == "!shuffle":
        q = get_queue(message.guild.id)

        if not q.queue:
            await message.channel.send("ko co queue!")
            return True

        q.shuffle()
        await message.channel.send("Shuffle queueeueueu!")
        return True
    if content == "!autoplay":
        q = get_queue(message.guild.id)
        q.autoplay = not q.autoplay
        
        status = "**ON**" if q.autoplay else "**Off**"
        await message.channel.send(f"Autoplay: {status}")
        
        # Nếu đang bật autoplay mà bot không đang phát → tự động bắt đầu
        vc = message.guild.voice_client
        if q.autoplay and vc and not vc.is_playing() and not vc.is_paused():
            await play_next(bot, vc, message)
        
        return True 
    if content == "!clear":
        q = get_queue(message.guild.id)
        q.queue.clear()
        await message.channel.send("Queue cleared!")
        return True
    if content == "!leave":
        vc = message.guild.voice_client
        if not vc:
            await message.channel.send("Wyvern not in voice!")
            return True
        await vc.disconnect()
        await message.channel.send("Bye bro!")
        return True 
    if content == "!show":
        await show_commands(bot, message)
        return True 
    
    return False
async def show_commands(bot, message):
    prefix_cmds = [
        "`!play <song>` • Play music",
        "`!skip` • Skip current track",
        "`!stop` • Stop & clear queue",
        "`!queue` • Show queue",
        "`!loop` • Toggle loop",
        "`!shuffle` • Shuffle queue",
        "`!autoplay` • Auto play related songs",
        "`!back` • Play previous track",
        "`!volume <0-100>` • Adjust volume",
        "`!clear`",
        "`!leave`",
        "`!show` • Show this menu"
    ]

    slash_cmds = [
        f"`/{cmd.name}`"
        for cmd in bot.tree.get_commands()
    ]

    embed = discord.Embed(
        title="Wyvern Control Panel",
        description="Use commands below to control the music system",
        color=0x2b2d31
    )

    embed.add_field(
        name="━━━━━━━━━━ Music Commands ━━━━━━━━━━",
        value="\n".join(prefix_cmds),
        inline=False
    )

    embed.add_field(
        name="━━━━━━━━━━ Slash Commands ━━━━━━━━━━",
        value="\n".join(slash_cmds) if slash_cmds else "`None`",
        inline=False
    )

    embed.add_field(
        name="━━━━━━━━━━ Notes ━━━━━━━━━━",
        value=(
            "• Must be in the same channel with Wyvern\n"
            "• Volume range: **0 → 100**"
        ),
        inline=False
    )

    embed.set_footer(
        text=f"Requested by {message.author.display_name}",
        icon_url=message.author.display_avatar.url
    )

    embed.set_thumbnail(
        url="https://cataas.com/cat"
    )

    embed.set_author(
        name=bot.user.name,
        icon_url=bot.user.display_avatar.url
    )

    await message.channel.send(embed=embed)
