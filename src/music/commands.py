from src.music.player import play_music

async def handle_music(bot, message):
    content = message.content.strip()

    if content.startswith("!play"):
        search = content.replace("!play", "").strip()
        await play_music(bot, message, search)
        return True

    return False
