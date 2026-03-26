import asyncio
import re
import subprocess
from datetime import datetime
from src.logger import logger
from src.bridge import Bridge

class DSTDaySeasonHandler:
    def __init__(self, bridge: Bridge, config):
        self.bridge = bridge
        self.config = config
        self.master_screen = "dst_master"
        self.channel_id = config.data["discord"]["channel_id"]

    async def handle_event(self, event: str):
        """Xử lý khi có Join / Leave / Death"""
        now = datetime.now().strftime("%H:%M")

        # Gửi lệnh lấy Day + Season
        cmd = f'print(string.format("SYNC|Day:%d|Season:%s", TheWorld.state.cycles + 1, TheWorld.state.season))\n'
        try:
            subprocess.run(["screen", "-S", self.master_screen, "-X", "stuff", cmd], check=True, timeout=5)
            await asyncio.sleep(1.0)
        except Exception as e:
            logger.error(f"Get day/season failed: {e}")

        # Tạm fallback (sau sẽ parse thật)
        day = "1"
        season = "Autumn"

        # Gửi thông báo
        msg = f"**{now}** | **Day {day} ({season})** | {event}"
        await self.bridge.send_to_discord("Server", msg)

        # Đổi tên kênh theo format bạn muốn: wynern-season-day
        await self.rename_channel(day, season)

    async def rename_channel(self, day: str, season: str):
        try:
            channel = self.bridge.discord.get_channel(self.channel_id)
            if channel:
                new_name = f"wynern-{season.lower()}-{day}"
                await channel.edit(name=new_name)
                logger.info(f"Channel renamed → {new_name}")
        except Exception as e:
            logger.error(f"Failed to rename channel: {e}")

    # Hàm gọi từ handler chính
    def request_event(self, event: str):
        asyncio.create_task(self.handle_event(event))
