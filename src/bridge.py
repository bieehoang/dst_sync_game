import asyncio
from src.logger import logger
from src.status_manager import setup_status   

class Bridge:
    def __init__(self, discord_client=None, dst_handler=None, bot=None):
        self.discord = discord_client
        self.dst = dst_handler
        self.bot = bot
        self.status_manager = None
        self.day_season = None

    async def setup_status(self):
        if not self.bot:
            logger.warning("Bridge: Where's bot?")
            return

        try:
            await setup_status(self.bot)
            logger.info(" Bridge: Setup done")
        except Exception as e:
            logger.error(f"Bridge: Fail to setup - {e}")

    async def send_to_game(self, username: str, message: str):
        if self.dst:
            self.dst.send_to_game(username, message)

    async def send_to_discord(self, username: str, message: str):
        if self.discord and hasattr(self.discord, 'config'):
            channel = self.discord.get_channel(self.discord.config.data["discord"]["channel_id"])
            if channel:
                full_msg = f"**{username}**: {message}"
                await channel.send(full_msg)
                logger.info(f"→ Discord: {username}: {message}")
            else:
                logger.error("Do not see Discord channel")
    def get_players(self):
        if hasattr(self.dst, "players"):
            if isinstance(self.dst.players, dict):
                return dict(self.dst.players)      # copy
            elif isinstance(self.dst.players, set):
                return {name: "Unknown" for name in self.dst.players}
        return {} 
    def kick_command(self, player_id: str) -> bool:
        if not self.dst:
            logger.error("[BRIDGE] Dst didn't ready")
            return False
        try:
            command = f'TheNet:Kick("{player_id}")'
            return self.dst.send_console(command)  # ← dùng send_console thay vì send_to_game
        except Exception as e:
            logger.error(f"[BRIDGE] Error: {e}")
            return False
