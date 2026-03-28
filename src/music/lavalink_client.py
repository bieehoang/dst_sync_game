import wavelink
from src.logger import logger

class LavalinkClient:
    def __init__(self, bot):
        self.bot = bot

    async def connect(self):
        try:
            node = wavelink.Node(
                uri="http://127.0.0.1:2333",
                password="youshallnotpass"
            )
            await wavelink.Pool.connect(client=self.bot, nodes=[node])
            logger.info("✅ Lavalink node connected successfully!")
            print("✅ Lavalink node connected successfully!")
        except Exception as e:
            logger.error(f"❌ Lavalink connect failed: {e}")
            print(f"❌ Lavalink connect failed: {e}")
