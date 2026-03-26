import discord
from src.bridge import Bridge
from src.logger import logger
from src.status_manager import setup_status   # ← THÊM DÒNG NÀY

class DiscordHandler(discord.Client):
    def __init__(self, bridge: Bridge, config):
        # Khai báo intents rõ ràng
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        self.bridge = bridge
        self.config = config

    async def on_ready(self):
        logger.info(f"✅ Discord bot logged in as {self.user} | ID: {self.user.id}")
        
        # ==================== SETUP STATUS MIMU + DST ====================
        if self.bridge:
            # Gán bot (Client) vào bridge
            self.bridge.bot = self
            
            # Set status MimU style
            await setup_status(self)
            
            logger.info("Activities actived")
        else:
            logger.warning("Bridge not built yet")

    async def on_message(self, message):
        if message.channel.id != self.config.data["discord"]["channel_id"] or message.author.bot:
            return
        
        content = message.content.strip()
        if content:
            await self.bridge.send_to_game(str(message.author.display_name), content)
            logger.info(f"← From Discord: {message.author.display_name}: {content}")
    

        ALLOWED_ROLE_IDS = {
        1385632295498678312,
        1385907308235718656,
        1385632574470226081
        }
        if message.author.bot:
            return

        if message.channel.id != self.config.data["discord"]["channel_id"]:
            return

        content = message.content.strip()

        # 🔥 check role (multi role)
        has_permission = any(role.id in ALLOWED_ROLE_IDS for role in message.author.roles)

        # ❌ block nếu không có quyền
        if content.startswith("!rb") and not has_permission:
            await message.channel.send("Find someone can be help")
            return

        # ✅ gửi vào game
        await self.bridge.send_to_game(str(message.author.display_name), content)
