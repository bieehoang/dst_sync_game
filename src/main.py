import asyncio
from src.config import Config
from src.logger import logger
from src.discord_handler import DiscordHandler
from src.bridge import Bridge
from src.dst_chat_handler import DSTChatHandler
from src.dst_day_season import DSTDaySeasonHandler
from src.dst_log_handler import DSTLogHandler

async def main():
    config = Config()
    bridge = Bridge()

    discord_bot = DiscordHandler(bridge, config)
    chat_handler = DSTChatHandler(bridge, config)
    day_season_handler = DSTDaySeasonHandler(bridge, config)
    log_handler = DSTLogHandler(bridge, config)

    bridge.discord = discord_bot
    bridge.day_season = day_season_handler
    bridge.dst = chat_handler   
    logger.info("Starting DST Discord Sync (REALTIME MODE)...")

    await asyncio.gather(
        discord_bot.start(config.discord_token),
        chat_handler.start(),
        log_handler.start(),
    )

if __name__ == "__main__":
    asyncio.run(main())
