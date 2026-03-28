import discord
from src.bridge import Bridge
from src.logger import logger
from src.status_manager import setup_status   
import commands.players as players_cmd
from src.weather_status import WeatherStatus
from commands.weather import setup as setup_weather
from commands.kick import setup as setup_kick
from src.music.lavalink_client import LavalinkClient
from src.music.player import play_music
from src.music.commands import handle_music 

class DiscordHandler(discord.Client):
    def __init__(self, bridge: Bridge, config):
        # Khai báo intents rõ ràng
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(intents=intents)
        
        self.bridge = bridge
        self.config = config
        self.tree = discord.app_commands.CommandTree(self) 
        self.weather_status = WeatherStatus(self) 
    async def on_ready(self):
        logger.info(f" Discord bot logged in as {self.user} | ID: {self.user.id}")
        
        self.lavalink = LavalinkClient(self)
        await self.lavalink.connect()        
        
        GUILD_ID = 1369692222735257721
        
        players_cmd.setup(self.tree, self.bridge)
        setup_weather(self.tree, self) 
        setup_kick(self.tree, self.bridge)
        guild = discord.Object(id=GUILD_ID)
        self.tree.clear_commands(guild=guild)
        self.tree.copy_global_to(guild=guild)

        await self.tree.sync(guild=guild)

        logger.info(f"Commands: {[cmd.name for cmd in self.tree.get_commands()]}") 

        # ==================== SETUP STATUS MIMU + DST ====================
        if self.bridge:
            # Gán bot (Client) vào bridge
            self.bridge.bot = self
            
            # Set status MimU style
            await setup_status(self)
            
            logger.info("Activities actived")
        else:
            logger.warning("Bridge not built yet")
        weather = WeatherStatus(self)
        self.loop.create_task(weather.update_status_loop())
    
    async def on_socket_response(self, payload):
        await handle_socket(payload) 
    
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id != int(self.config.data["discord"]["channel_id"]):
            return

        content = message.content.strip()
        if not content:
            return
        if await handle_music(self, message):
            return

        ALLOWED_ROLE_IDS = {
        1385632295498678312,
        1385907308235718656,
        1385632574470226081
        }

        # 🔥 check role cho command
        has_permission = any(role.id in ALLOWED_ROLE_IDS for role in message.author.roles)

        if content.startswith("!rb"):
            if not has_permission:
                await message.channel.send("Maybe someone can help? <@&1385632574470226081>")
                return
            await message.channel.send("Roi nha")
        await self.bridge.send_to_game(str(message.author.display_name), content)

        logger.info(f"← From Discord: {message.author.display_name}: {content}")
