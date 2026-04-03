import asyncio
import re
import subprocess
from datetime import datetime
from src.logger import logger
from src.bridge import Bridge

class DSTHandler:
    def __init__(self, bridge: Bridge, config):
        self.bridge = bridge
        self.config = config
        self.bot_prefix = config.data["discord"]["bot_prefix"]
        self.master_screen = "dst_master"
        self.log_path = "/home/steam/.klei/DoNotStarveTogether/MyDediServer/Master/server_chat_log.txt"

    async def start_monitor(self):
        logger.info("Simple DST Sync Bot started")
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
        now = datetime.now().strftime("%H:%M")

        # 1. Chat từ game → Discord
        if m := re.search(r'\[Say\].*?\)\s*(.+?)\s*:\s*(.+)', line):
            username = m.group(1).strip()
            msg = m.group(2).strip()
            if msg and not msg.startswith(self.bot_prefix):
                await self.bridge.send_to_discord(username, msg)
                logger.info(f"Game → Discord: {username}: {msg}")
            return

        # 2. Join / Leave / Death
        event = None
        if m := re.search(r'\[Join Announcement\]\s*(.+)', line):
            event = f"{m.group(1).strip()} has joined the server"
        elif m := re.search(r'\[Leave Announcement\]\s*(.+)', line):
            event = f"{m.group(1).strip()} has left the server"
        elif m := re.search(r'\[Death Announcement\]\s*(.+)', line):
            event = m.group(1).strip()

        if event:
            await self.bridge.send_to_discord("Server", f"**{now}** | {event}")
            logger.info(f"Event sent: {event}")

    # Gửi tin từ Discord vào game
    def send_to_game(self, username: str, message: str):
        cmd = self.config.data["dst"]["announce_command"].format(
            prefix=self.bot_prefix, username=username, message=message.replace('"', '\\"')
        )
        try:
            subprocess.run(["screen", "-S", self.master_screen, "-X", "stuff", cmd + "\n"], check=True, timeout=5)
            logger.info(f"Discord → Game: {username}: {message}")
        except Exception as e:
            logger.error(f"Send to game failed: {e}")
