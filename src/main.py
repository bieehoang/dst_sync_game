import asyncio
from src.config import Config
from src.logger import logger
from src.discord_handler import DiscordHandler
from src.bridge import Bridge
from src.dst_chat_handler import DSTChatHandler
from src.dst_sync_handler import DSTSyncHandler

async def main():
    config = Config()
    bridge = Bridge()

    discord_bot = DiscordHandler(bridge, config)
    chat_handler = DSTChatHandler(bridge, config)
    sync_handler = DSTSyncHandler(bridge, config)

    bridge.discord = discord_bot

    logger.info("Starting DST Discord Sync with separate handlers...")

    await asyncio.gather(
        discord_bot.start(config.discord_token),
        chat_handler.start(),
        sync_handler.start()
    )

if __name__ == "__main__":
    asyncio.run(main())
