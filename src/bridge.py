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
        """Setup status MimU style"""
        if not self.bot:
            logger.warning("Bridge: Không có bot để set status")
            return

        try:
            await setup_status(self.bot)                    # Gọi hàm setup từ status_manager
            logger.info("✅ Bridge: Đã setup Discord status MimU thành công")
        except Exception as e:
            logger.error(f"Bridge: Lỗi setup status - {e}")

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
