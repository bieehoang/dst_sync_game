import asyncio
import re
from datetime import datetime
from src.logger import logger
from src.bridge import Bridge

class DSTSyncHandler:
    def __init__(self, bridge: Bridge, config):
        self.bridge = bridge
        self.config = config
        self.log_path = "/home/steam/.klei/DoNotStarveTogether/MyDediServer/Master/server_log.txt"

    async def start(self):
        logger.info(f"Sync Handler started - {self.log_path}")
        proc = await asyncio.create_subprocess_exec(
            "tail", "-F", "-n", "0", self.log_path,
            stdout=asyncio.subprocess.PIPE
        )

        while True:
            line = await proc.stdout.readline()
            if not line:
                await asyncio.sleep(1)
                continue
            line = line.decode("utf-8", errors="ignore").strip()
            if line:
                await self.parse_sync(line)

    async def parse_sync(self, line: str):
        if "SYNC|" not in line:
            return

        logger.info(f"Found SYNC raw: {line}")

        m = re.search(r'SYNC\|Day:(\d+)\|Season:(\w+).*?\|Event:(.+)', line)
        if m:
            day, season, event = m.groups()
            season = season.capitalize()
            now = datetime.now().strftime("%H:%M")
            msg = f"**{now}** | **Day {day} ({season})** | {event}"
            await self.bridge.send_to_discord("Server", msg)
            logger.info(f"→ Sent to Discord: {msg}")
