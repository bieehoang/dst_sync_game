# src/status_manager.py
import asyncio
import discord
from src.logger import logger


class StatusManager:
    """
    Quản lý trạng thái Discord bot (giống MimU + DST)
    Hỗ trợ cả discord.Client và commands.Bot
    """

    def __init__(self, bot):
        self.bot = bot   # có thể là Client hoặc Bot

    async def set_mimu_style_status(self):
        """Set trạng thái chính giống MimU"""
        if not self.bot or not self.bot.is_ready():
            logger.warning("Bot chưa ready để set status")
            return

        try:
            await self.bot.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name="Wyvern • Mesa-Linux Server"
                )
            )
            logger.info("✅ Đã set status MimU style: /help • discord.gg/wyvern • DST Dedicated Server")
        except Exception as e:
            logger.error(f"Lỗi set MimU status: {e}")

    async def start_rotation(self, interval: int = 60):
        """Luân phiên status (tùy chọn)"""
        async def rotate():
            activities = [
                discord.Activity(type=discord.ActivityType.playing, name="Wyvern"),
                discord.Activity(type=discord.ActivityType.playing, name="Mesa-Linux"),
                discord.Activity(type=discord.ActivityType.playing, name="Don't Starve Together"),
            ]
            i = 0
            while True:
                try:
                    await self.bot.change_presence(
                        status=discord.Status.online,
                        activity=activities[i % len(activities)]
                    )
                    i += 1
                except Exception as e:
                    logger.error(f"Rotate status error: {e}")
                await asyncio.sleep(interval)

        asyncio.create_task(rotate())
        logger.info(f"🔄 Đã bật rotate status mỗi {interval} giây")


# ==================== Hàm setup nhanh ====================
async def setup_status(bot):
    """Gọi hàm này để setup status"""
    manager = StatusManager(bot)
    await manager.set_mimu_style_status()
    await manager.start_rotation(interval=50)   # bỏ comment nếu muốn luân phiên
    return manager
