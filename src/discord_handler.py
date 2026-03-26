import discord
from src.bridge import Bridge
from src.logger import logger

class DiscordHandler(discord.Client):
    def __init__(self, bridge: Bridge, config):
        # Khai báo intents rõ ràng
        intents = discord.Intents.default()
        intents.message_content = True   # Bắt buộc để đọc tin nhắn
        super().__init__(intents=intents)
        self.bridge = bridge
        self.config = config

    async def on_ready(self):
        logger.info(f"✅ Discord bot logged in as {self.user} | ID: {self.user.id}")

    async def on_message(self, message):
        if message.channel.id != self.config.data["discord"]["channel_id"] or message.author.bot:
            return
        
        content = message.content.strip()
        if content:
            await self.bridge.send_to_game(str(message.author.display_name), content)
            logger.info(f"← From Discord: {message.author.display_name}: {content}")
