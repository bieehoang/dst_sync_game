import asyncio
from src.logger import logger
from src.status_manager import setup_status   # Dùng setup_status thay vì StatusManager trực tiếp

class Bridge:
    def __init__(self, discord_client=None, dst_handler=None, bot=None):
        self.discord = discord_client
        self.dst = dst_handler
        self.bot = bot
        self.status_manager = None
        self.day_season = None

    async def setup_status(self):
        """Setup status style"""
        if not self.bot:
            logger.warning("Bridge: Where's bot?")
            return

        try:
            await setup_status(self.bot)
            logger.info(" Bridge: Setup done")
        except Exception as e:
            logger.error(f"Bridge: Fail to setup - {e}")

    async def send_to_game(self, username: str, message: str):
        if self.dst:
            self.dst.send_to_game(username, message)

    async def send_to_discord(self, username: str, message: str):
        if self.discord and hasattr(self.discord, 'config'):
            channel = self.discord.get_channel(self.discord.config.data["discord"]["channel_id"])
            if channel:
                full_msg = f"**{username}**: {message}"
                await channel.send(full_msg)
                logger.info(f"→ Discord: {username}: {message}")
            else:
                logger.error("Do not see Discord channel")
    def get_players(self):
        if self.dst and hasattr(self.dst, "players"):
            return list(self.dst.players)
        return []
