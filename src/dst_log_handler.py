import asyncio
import re
from src.logger import logger

class DSTLogHandler:
    def __init__(self, bridge, config):
        self.bridge = bridge
        self.config = config
        self.log_path = "/home/steam/.klei/DoNotStarveTogether/MyDediServer/Master/server_log.txt"

    async def start(self):
        logger.info(f"[LOG] Listening {self.log_path}")

        proc = await asyncio.create_subprocess_exec(
            "tail", "-F", "-n", "0", self.log_path,
            stdout=asyncio.subprocess.PIPE
        )

        while True:
            line = await proc.stdout.readline()
            if not line:
                await asyncio.sleep(0.2)
                continue

            line = line.decode("utf-8", errors="ignore").strip()
            await self.parse_line(line)

    async def parse_line(self, line: str):
        # 🔥 Parse SYNC
        if m := re.search(r'SYNC\|Day:(\d+)\|Season:(\w+)', line):
            day = m.group(1)
            season = m.group(2)

            logger.info(f"[SYNC] Day {day} | {season}")

            if hasattr(self.bridge, "day_season"):
                await self.bridge.day_season.update(day, season)
