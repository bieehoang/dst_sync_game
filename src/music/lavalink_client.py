import wavelink
import asyncio
from src.logger import logger

class LavalinkClient:
    def __init__(self, bot):
        self.bot = bot

    async def connect(self):
        try:
            logger.info("🔄 Connecting to Lavalink on http://127.0.0.1:2333...")

            node = wavelink.Node(
                uri="http://127.0.0.1:2333",
                password="youshallnotpass"
            )

            await wavelink.Pool.connect(client=self.bot, nodes=[node])

            # Chờ node sẵn sàng (tương thích nhiều phiên bản wavelink)
            await asyncio.sleep(4)

            # Kiểm tra node
            if wavelink.Pool.nodes:
                logger.info("✅ Lavalink connected successfully!")
                print("✅ Lavalink connected successfully!")
            else:
                logger.error("❌ No Lavalink node is connected")
                print("❌ No Lavalink node is connected")

        except Exception as e:
            logger.error(f"❌ Lavalink connection failed: {e}")
            print(f"❌ Lavalink connection failed: {e}")
