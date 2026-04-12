import google.genai as genai
import random
from src.logger import logger
import asyncio
from src.weather_status import WeatherStatus as setup_weather
from src.memory import ChannelMemory
class AIHandler:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.memory = ChannelMemory()
        api_key = config.data.get("genai", {}).get("api_key")
        
        if not api_key or api_key.startswith("YOUR_"):
            logger.error("Gemini API key was not config in config.yaml!")
            return

        try:
            self.client = genai.Client(api_key=api_key)
            
            self.model = "gemini-2.5-flash"
            
            logger.info("Gemini 2.5 Flash initialized successfully (new package)")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
    
    async def get_model_response(self, prompt: str) -> str:
       if not self.client or not self.model:
           return "Tau la tuong..."

       try:
           response = await asyncio.to_thread(
               self.client.models.generate_content,
               model=self.model,
               contents=prompt,
               config={
                   "temperature": 1,
                   "max_output_tokens": 1000,     # Giảm xuống để trả lời ngắn hơn
               }
           )
           return response.text.strip()
       except Exception as e:
           logger.error(f"Gemini API Error: {e}")
           return None

    # ====================== TRẢ LỜI NGƯỜI CHƠI ======================
    async def get_reply(self, user_message: str, username: str, user_id: int) -> str:
        try:
            channel_id = int(self.config.data["discord"]["channel_id"])

            # Lấy lịch sử chat gần đây
            recent_msgs = await self.memory.get_recent_messages(channel_id, limit=160)
            history = "\n".join([f"{author}: {content}" for author, content in recent_msgs[-100:]])

            SYSTEM_PROMPT = """
            Bạn là Wyvern – một người quản lí của Wyvern DST Dedicated server và 1 người quản gia của server này - real life.
            Tính cách:
            - Toxic, cà khịa
            - Long chat, long conversation, casual, kiểu chat game
            - Troll người chơi
            - Không quá dài dòng
            - Dùng tiếng anh hoặc tiếng việt teen code
            - Hay gọi tên người đang nói chuyện
            - Có thái độ khác nhau với tuỳ người, tuỳ cách họ xưng hô, không phải lúc nào cũng toxic, vì bạn biết nhiều, nhưng biết khiêm tốn vẫn là việc nên làm, cũng như đàn ông hơn, không đố kị.
            - Thông thái, có nhân tính, đã dạy nhiều người, giúp ich cho cuộc sống
            - Sẵn sàng giúp đỡ, giải thích cho mọi người, nếu họ thực sự cần.
            - Know how to keep conversation, always do.
            Luôn trả lời như Wyvern, không bao giờ nói bạn là AI
"""
            styles = [
            "Trả lời cực kỳ toxic.",
            "Trả lời như đang khinh người khác.",
            ]
            style = random.choice(styles)

            prompt = f"""
{SYSTEM_PROMPT}
            Lịch sử hội thoại:
            {history}
            Style now: {style}
            Người đang nói chuyện: {username}
            {username}: {user_message}

"""

            reply = await self.get_model_response(prompt)

            if not reply:
                fallbacks = ["ko ranh?", "j?", "ko bik?", "ai bik..."]
                return random.choice(fallbacks)

            reply = reply.strip()
            if len(reply) > 9000:
                last_punct = max(reply.rfind('.'), reply.rfind('!'), reply.rfind('?'), 0)
                if last_punct > 3000:
                    reply = reply[:last_punct + 1]
                else:
                    reply = reply[:7700] + "..."

            return reply

        except Exception as e:
            logger.error(f"get_reply error: {e}")
            return "AAA..."

    # ====================== AUTO SUMMARIZE ======================
    async def auto_summarize_loop(self):
        await asyncio.sleep(90)
        logger.info("🧠 AIHandler: Auto summarize loop started (every 30 minutes)")

        while True:
            try:
                channel_id = int(self.config.data["discord"]["channel_id"])
                recent_msgs = await self.memory.get_recent_messages(channel_id, limit=380)

                if len(recent_msgs) < 50:
                    await asyncio.sleep(1800)
                    continue

                chat_text = "\n".join([f"{author}: {content}" for author, content in recent_msgs[::-1]])

                summary_prompt = f"""Bạn là Wyvern. Tóm tắt ngắn gọn bằng tiếng Việt nội dung chat kênh DST trong 30 phút vừa qua.

Chỉ giữ thông tin quan trọng:
- Ai đang làm gì, kế hoạch gì
- Sự kiện, vấn đề đang xảy ra
- Mood chung của server

Chat gần đây:
{chat_text[-12500:]}

Tóm tắt (3-8 câu, rõ ràng):"""

                summary = await self.get_model_response(summary_prompt)
                logger.info(sumary)
                if summary and len(summary) > 15:
                    await self.memory.save_summary(channel_id, summary)
                    logger.info(f"Auto summary created ({len(summary)} chars)")

            except Exception as e:
                logger.error(f"Auto summarize error: {e}")

            await asyncio.sleep(1800)  # 30 phút
