import discord
from src.bridge import Bridge
from src.logger import logger
from src.status_manager import setup_status   
import commands.players as players_cmd
from src.weather_status import WeatherStatus
from commands.weather import setup as setup_weather
from commands.kick import setup as setup_kick
from commands.update import setup as setup_update
from src.music.commands import handle_music 
from discord.ext import commands
from src.ai_handler import AIHandler

class DiscordHandler(commands.Bot):
    def __init__(self, bridge: Bridge, config):
        # Khai báo intents rõ ràng
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(
                command_prefix="!",
                intents=intents
                )
        
        self.bridge = bridge
        self.config = config
        self.weather_status = WeatherStatus(self) 
        self.ai_handler = AIHandler(self.config)
        self.ai_handler.weather = self.weather_status
    async def on_ready(self):
        #if self._ready:
            #logger.warning("Skipping - on_ready was called")
            #return
        #self._ready = True
        logger.info(f" Discord bot logged in as {self.user} | ID: {self.user.id}")
        
        #GUILD_ID = 1369692222735257721
        players_cmd.setup(self.tree, self.bridge)
        setup_weather(self.tree, self) 
        setup_kick(self.tree, self.bridge)
        await setup_update(self.tree, self.bridge) 
        #guild = discord.Object(id=GUILD_ID)
        #self.tree.clear_commands(guild=guild)
        #self.tree.copy_global_to(guild=guild)
        
        #await self.tree.sync(guild=guild)
        #sync global 
        await self.tree.sync()

        logger.info(f"Global Commands: {[cmd.name for cmd in self.tree.get_commands()]}") 

        if self.bridge:
            self.bridge.bot = self
            
            await setup_status(self)
            
            logger.info("Wyvern's Status Actived")
        else:
            logger.warning("Bridge not built yet")
        weather = WeatherStatus(self)
        self.loop.create_task(weather.update_status_loop())
        self.loop.create_task(weather.update_readme_loop())
        self.loop.create_task(self.ai_handler.auto_summarize_loop())
    
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
        if hasattr(self, 'memory'):
            await self.memory.add_message(
                message.channel.id,
                message.id,
                message.author.display_name,
                content
            )
        lower_content= content.lower()
        if (
            message.guild.me.mentioned_in(message)
            or lower_content.startswith(("wyvern", "hey wyvern", "wyvern oi"))
            ):
            parts = content.split(maxsplit=1)
            clean_msg = parts[1] if len(parts) > 1 else ""
            if not clean_msg:
                clean_msg = "hoi gi di?"
            reply = await self.ai_handler.get_reply(
                clean_msg,
                message.author.display_name,
                message.author.id
                )
            if reply:
                await message.channel.send(reply)
            logger.info(f"AI replied to {message.author.display_name}: {clean_msg[:50]}...") 
        
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
        if await handle_music(self, message):
            return
        logger.info(f"← From Discord: {message.author.display_name}: {content}")
