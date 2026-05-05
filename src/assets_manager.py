# src/assets_manager.py
import discord
import os
from src.logger import logger

class AssetsManager:
    def __init__(self):
        self.wyvern_gif_url: str | None = None

    async def load(self, bot: discord.Client, channel_id: int):
        """Upload gif lên Discord 1 lần khi bot start, cache URL lại."""
        gif_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "wyvern.gif")

        if not os.path.exists(gif_path):
            logger.error(f"[ASSETS] Log Path: {gif_path}")
            return

        try:
            channel = bot.get_channel(channel_id)
            if not channel:
                logger.error("[ASSETS] Không tìm thấy channel để upload gif")
                return

            msg = await channel.send(file=discord.File(gif_path))
            self.wyvern_gif_url = msg.attachments[0].url
            await msg.delete()

            logger.info(f"[ASSETS] Gif uploaded & cached: {self.wyvern_gif_url}")

        except Exception as e:
            logger.error(f"[ASSETS] Load gif failed: {e}")

assets = AssetsManager()
