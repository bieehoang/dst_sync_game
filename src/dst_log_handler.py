import asyncio
import re
import os
from src.logger import logger
from src.bridge import Bridge


class DSTLogHandler:
    def __init__(self, bridge: Bridge, config):
        self.bridge = bridge
        self.config = config
        self.log_path = "/home/steam/.klei/DoNotStarveTogether/MyDediServer/Master/server_log.txt"

    async def start(self):
        logger.info(f"[LOG] Listening server_log.txt: {self.log_path}")

        if not os.path.exists(self.log_path):
            logger.error(f"[LOG] Cannot find server_log.txt at {self.log_path}")
            return

        proc = await asyncio.create_subprocess_exec(
            "tail", "-F", "-n", "0", self.log_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                line = line.decode("utf-8", errors="ignore").strip()
                if line:
                    await self.parse_line(line)

        except asyncio.CancelledError:
            proc.kill()
            await proc.wait()
        except Exception as e:
            logger.error(f"[LOG] Error in DSTLogHandler: {e}")
            proc.kill()

    async def parse_line(self, line: str):
        """Parse các thông tin từ server_log.txt"""

        # ================== CLIENT AUTHENTICATED (LẤY KU_ID) ==================
        if "Client authenticated:" in line:
            if m := re.search(r'Client authenticated:\s*\(KU_([a-zA-Z0-9]+)\)\s*(.+)', line):
                ku_id = f"KU_{m.group(1)}"
                username = m.group(2).strip()

                if hasattr(self.bridge.dst, "players"):
                    if not isinstance(self.bridge.dst.players, dict):
                        self.bridge.dst.players = {}
                    self.bridge.dst.players[username] = ku_id

                logger.info(f"[AUTH] {username} authenticated | KU_ID: {ku_id}")
                return

        # ================== SYNC Day & Season (SỬA REGEX) ==================
        if "SYNC" in line or "Day" in line:
            # Regex mới phù hợp với format log của bạn
            if m := re.search(r'Day[:\s]+(\d+)', line):
                day = m.group(1)
                season = "unknown"

                # Tìm season
                if "winter" in line.lower():
                    season = "Winter"
                elif "spring" in line.lower():
                    season = "Spring"
                elif "summer" in line.lower():
                    season = "Summer"
                elif "autumn" in line.lower() or "fall" in line.lower():
                    season = "Autumn"

                logger.info(f"[SYNC] Day {day} | Season: {season}")

                if hasattr(self.bridge, "day_season"):
                    await self.bridge.day_season.update(day, season)
                return                
