import asyncio
from src.logger import logger

class Bridge:
    def __init__(self, discord_client=None, dst_handler=None):
        self.discord = discord_client
        self.dst = dst_handler

    async def send_to_game(self, username: str, message: str):
        if self.dst:
            self.dst.send_to_game(username, message)

    async def send_to_discord(self, username: str, message: str):
        if self.discord:
            channel = self.discord.get_channel(self.discord.config.data["discord"]["channel_id"])
            if channel:
                full_msg = f"**{username}**: {message}"
                await channel.send(full_msg)
                logger.info(f"→ Discord: {username}: {message}")
