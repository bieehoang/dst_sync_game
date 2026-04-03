import asyncio
import re
import subprocess
from src.logger import logger
from src.bridge import Bridge
class DSTChatHandler:
    def __init__(self, bridge: Bridge, config):
        self.bridge = bridge
        self.config = config
        self.bot_prefix = config.data["discord"]["bot_prefix"]
        self.log_path = "/home/steam/.klei/DoNotStarveTogether/MyDediServer/Master/server_chat_log.txt"
        self.screen_name = self.get_master_screen() 
        self.status_manager=None
        self.players = {} 
    def get_master_screen(self):
        try:
            result = subprocess.check_output(["screen", "-ls"]).decode()

            for line in result.splitlines():
                line = line.strip()
                if ".dst_master" in line:
                    screen_name = line.split()[0]
                    print(f"[DEBUG] Found screen: {screen_name}")
                    return screen_name
            
        except Exception as e:
            from src.logger import logger
            logger.error(f"Get screen failed: {e}")

        return "dst_master"
    async def start(self):
        logger.info(f"Chat Handler started - {self.log_path}")

        if self.bridge and hasattr(self.bridge, 'bot') and self.bridge.bot:
            try:
                self.status_manager = await setup_status(
                    bot=self.bridge.bot,
                    use_rotation=True
                )
            except Exception as e:
                logger.error(f"Setup status fail: {e}")
        else:
            logger.warning("Passing")

        proc = await asyncio.create_subprocess_exec(
            "tail", "-F", "-n", "0", self.log_path,
            stdout=asyncio.subprocess.PIPE
        )

        logger.info("Watching server_chat_log.txt...")

        while True:
            line = await proc.stdout.readline()
            if not line:
                await asyncio.sleep(0.2)
                continue

            line = line.decode("utf-8", errors="ignore").strip()

            if line:
                await self.parse_line(line) 
    async def parse_line(self, line: str):

        if m := re.search(r'\[Say\].*?\)\s*(.*?):\s*(.*)', line):
            username = m.group(1).strip()
            msg = m.group(2).strip()

            if msg and not msg.startswith(self.bot_prefix):
                await self.bridge.send_to_discord(username, msg)
                logger.info(f"Chat: {username}: {msg}")
            return
    # Chat người chơi
        if m := re.search(r'\[Say\].*?:\s*(.+?):\s*(.+)', line):
            username = m.group(1).strip()
            msg = m.group(2).strip()

            if msg and not msg.startswith(self.bot_prefix):
                await self.bridge.send_to_discord(username, msg)
                logger.info(f"Chat: {username}: {msg}")
            return
        # Join Announcement
        if m := re.search(r'\[Join Announcement\]\s*(.+)', line):
            username = m.group(1).strip()
            self.bridge.day_season.request_event(f"**{username}** Joined")
            logger.info(f"Join detected: {username}")
            return

        # Leave Announcement
        if m := re.search(r'\[Leave Announcement\]\s*(.+)', line):
            username = m.group(1).strip()
            self.bridge.day_season.request_event(f"**{username}** Leave")
            logger.info(f"Leave detected: {username}")
            return

        # Death Announcement
        if m := re.search(r'\[Death Announcement\]\s*(.+)', line):
            death_text = m.group(1).strip()
            self.bridge.day_season.request_event(f"{death_text}")
            logger.info(f"Death detected: {death_text}")
            return
    
    def send_to_game(self, username: str, message: str):
        import subprocess

        message = message.strip()
        screen_name = self.get_master_screen()

        if any(cmd in message for cmd in ["TheNet:", "c_", "TheSim:", "c_rollback", "c_regenerate"]):
            cmd = message + "\r"
            logger.info(f"[CONSOLE] {username} → {message}")

        elif message.startswith("!rb"):
            try:
                parts = message.split()
                days = int(parts[1]) if len(parts) > 1 else 1
                cmd = f'c_rollback({days})\r'
                logger.info(f"[ROLLBACK] {username} → {days} days")
            except Exception:
                cmd = 'c_rollback(1)\r'
                logger.warning(f"[ROLLBACK] {username} → invalid, default 1")

        else:
            message = message.replace('"', '\\"')
            cmd = f'c_announce("[Discord] {username}: {message}")\r'
            logger.info(f"→ To Game (Announce): {username}: {message}")

        try:
            subprocess.run([
                "screen",
                "-S", screen_name,
                "-p", "0",
                "-X", "stuff",
                cmd
            ], check=True, timeout=5)

            return True
        except subprocess.TimeoutExpired:
            logger.error(f"[SEND] Timeout when sending command to screen {screen_name}")
            return False
        except Exception as e:
            logger.error(f"[SEND] Failed to send to game: {e}")
            return False
