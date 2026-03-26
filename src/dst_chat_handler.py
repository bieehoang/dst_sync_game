import asyncio
import re
from src.logger import logger
from src.bridge import Bridge

class DSTChatHandler:
    def __init__(self, bridge: Bridge, config):
        self.bridge = bridge
        self.config = config
        self.bot_prefix = config.data["discord"]["bot_prefix"]
        self.log_path = "/home/steam/.klei/DoNotStarveTogether/MyDediServer/Master/server_chat_log.txt"

    async def start(self):
        logger.info(f"Chat Handler started - {self.log_path}")
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
                await self.parse_line(line)

    async def parse_line(self, line: str):
        # Chat người chơi
        if m := re.search(r'\[Say\].*?\)\s*(.+?)\s*:\s*(.+)', line):
            username = m.group(1).strip()
            msg = m.group(2).strip()
            if msg and not msg.startswith(self.bot_prefix):
                await self.bridge.send_to_discord(username, msg)
                logger.info(f"Chat: {username}: {msg}")
            return

        # Join Announcement
        if m := re.search(r'\[Join Announcement\]\s*(.+)', line):
            username = m.group(1).strip()
            await self.bridge.send_to_discord("Server", f" **{username}** Joined")
            logger.info(f"Join detected: {username}")
            return

        # Leave Announcement
        if m := re.search(r'\[Leave Announcement\]\s*(.+)', line):
            username = m.group(1).strip()
            await self.bridge.send_to_discord("Server", f" **{username}** Leave")
            logger.info(f"Leave detected: {username}")
            return

        # Death Announcement
        if m := re.search(r'\[Death Announcement\]\s*(.+)', line):
            death_text = m.group(1).strip()
            await self.bridge.send_to_discord("Death", f" {death_text}")
            logger.info(f"Death detected: {death_text}")
            return
