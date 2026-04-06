import asyncio
import subprocess
from datetime import datetime
from src.logger import logger

class DSTDaySeasonHandler:
    def __init__(self, bridge, config):
        self.bridge = bridge
        self.config = config
        self.master_screen = self.get_master_screen() 
        self.channel_id = config.data["discord"]["channel_id"]

        # State thật
        self.current_day = "?"
        self.current_season = "?"

        # Event chờ SYNC từ log handler
        self._event = asyncio.Event()

    def get_master_screen(self):
        result = subprocess.check_output(["screen", "-ls"]).decode()
        for line in result.splitlines():
            if ".dst_master" in line:
                return line.strip().split()[0]
        return "dst_master" 
    async def update(self, day, season):
        self.current_day = day
        self.current_season = season

        logger.info(f"[UPDATE] Day {day} | {season}")

        self._event.set()  # báo đã nhận data

    async def request_day_season(self):
        self._event.clear()

        cmd = 'print(string.format("SYNC|Day:%d|Season:%s", TheWorld.state.cycles + 1, TheWorld.state.season))\n'

        try:
            subprocess.run(
                ["screen", "-S", self.master_screen, "-X", "stuff", cmd],
                check=True
            )
        except Exception as e:
            logger.error(f"Send command failed: {e}")
            return None, None

        try:
            await asyncio.wait_for(self._event.wait(), timeout=3)
            return self.current_day, self.current_season
        except asyncio.TimeoutError:
            logger.error("SYNC timeout")
            return None, None

    async def handle_event(self, event: str):
        now = datetime.now().strftime("%H:%M")

        day, season = await self.request_day_season()

        if not day:
            day = "?"
            season = "?"

        msg = f"**Day {day} ({season})** | {event}"
        await self.bridge.send_to_discord("Server", msg)

        await self.rename_channel(day, season)

    async def rename_channel(self, day: str, season: str):
        try:
            channel = self.bridge.discord.get_channel(self.channel_id)
            if channel:
                new_name = f"𖦹﹒wyvern-{season.lower()}-{day}"
                await channel.edit(name=new_name)
                logger.info(f"Channel renamed → {new_name}")
        except Exception as e:
            logger.error(f"Rename failed: {e}")

    def request_event(self, event: str):
        asyncio.create_task(self.handle_event(event))
