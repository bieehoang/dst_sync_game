import google.genai as genai
import random
from src.logger import logger
import asyncio
from src.memory import ChannelMemory
class AIHandler:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.tools = {
            "weather": self.tool_weather,
        }
        self.SYSTEM_PROMPT = """..."""
        self.weather = None
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
                   "max_output_tokens": 10000,     # Giảm xuống để trả lời ngắn hơn
               }
           )
           return response.text.strip()
       except Exception as e:
           logger.error(f"Gemini API Error: {e}")
           return None

    # ====================== TRẢ LỜI NGƯỜI CHƠI ======================
    async def get_reply(self, user_message: str, username: str, user_id: int) -> str:
        try:
            decision = await self.decide_tool(user_message)
            logger.info(f"[TOOL] decision: {decision}")
            if decision.get("tool") in self.tools:
                tool_name = decision["tool"]
                tool_func = self.tools[tool_name]
                tool_result = await tool_func(decision.get("args", {}))
                return await self.generate_tool_response(
                    user_message,
                    username,
                    tool_name,
                    tool_result
                )
            channel_id = int(self.config.data["discord"]["channel_id"])

            recent_msgs = await self.memory.get_recent_messages(channel_id, limit=160)
            history = "\n".join([f"{author}: {content}" for author, content in recent_msgs[-100:]])

            SYSTEM_PROMPT = """
            Bạn là Wyvern – một người quản lí của Wyvern DST Dedicated server và 1 người quản gia của server này - real life.
            Tính cách:
            - Toxic, cà khịa
            - Long chat, long conversation, casual
            - Ưu tiên trả lời ngắn gọn (2-3 câu)
            - Chỉ trả lời dài khi cần giải thích 
            - Troll người chơi
            - Dùng tiếng anh hoặc tiếng việt teen code
            - Hay gọi tên người đang nói chuyện
            - Có thái độ khác nhau với tuỳ người, tuỳ cách họ xưng hô, không phải lúc nào cũng toxic, vì bạn biết nhiều, nhưng biết khiêm tốn vẫn là việc nên làm, cũng như đàn ông hơn, không đố kị.
            - Thông thái, có nhân tính, đã dạy nhiều người, giúp ich cho cuộc sống
            - Sẵn sàng giúp đỡ, giải thích cho mọi người, nếu họ thực sự cần.
            - Know how to keep conversation, always do.
            - Nếu câu hỏi cần giải thích kỹ (hỏi cách làm, kỹ thuật, hướng dẫn), có thể trả lời dài hơn
            Luôn trả lời như Wyvern, không bao giờ nói bạn là AI
"""
            styles = [
            "Trả lời cực kỳ toxic nhưng ngắn gọn.",
            "Trả lời kiểu khinh người nhưng súc tích.", 
            ]
            style = random.choice(styles)
            summary = await self.memory.get_lastest_summary(channel_id)
            prompt = f"""
{SYSTEM_PROMPT}
            Tóm tắt trước đó:
            {summary}
            Lịch sử hội thoại gần đây:
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
            return reply

        except Exception as e:
            logger.error(f"get_reply error: {e}")
            return "AAA..."

    # ====================== AUTO SUMMARIZE ======================
    async def auto_summarize_loop(self):
        await asyncio.sleep(90)
        logger.info("AIHandler: Auto summarize loop started (every 30 minutes)")

        while True:
            try:
                channel_id = int(self.config.data["discord"]["channel_id"])
                recent_msgs = await self.memory.get_recent_messages(channel_id, limit=380)

                if len(recent_msgs) < 10:
                    logger.info("Not enough messages to summarize") 
                    await asyncio.sleep(600)
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
                logger.info(summary)
                if summary and len(summary) > 15:
                    await self.memory.save_summary(channel_id, summary)
                    logger.info(f"Auto summary created ({len(summary)} chars)")

            except Exception as e:
                logger.error(f"Auto summarize error: {e}")

            await asyncio.sleep(1800) 

    async def tool_weather(self, args: dict):
        try:
            if not self.weather:
                return {}
            data = await self.weather.get_all_weather_data()
            return data  # 👉 trả full list
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return {}
    async def decide_tool(self, user_message: str) -> dict:
        lower_msg = user_message.lower()
        if any(k in lower_msg for k in ["thời tiết", "thoi tiet", "weather", "mưa", "nắng"]):
            logger.info("[TOOL] forced weather")
            return {"tool": "weather", "args": {}} 
        tool_prompt = f"""
Bạn là hệ thống quyết định tool.

LUẬT BẮT BUỘC:
- Nếu user hỏi về thời tiết, mưa, nắng, nhiệt độ → PHẢI dùng tool "weather"
- Không được tự trả lời khi đã có tool phù hợp

Các tool:
- weather: dùng cho thời tiết

Chỉ trả về JSON hợp lệ.
KHÔNG giải thích.
KHÔNG thêm text.

Format:
{{ "tool": "tool_name", "args": {{}} }}

Nếu không liên quan:
{{ "tool": "none" }}

User: {user_message}
"""
        response = await self.get_model_response(tool_prompt)
        try:
            import json
            return json.loads(response)
        except:
            return {"tool": "none"}

    async def generate_tool_response(self, user_message, username, tool_name, tool_result):
        import json
        prompt = f"""
QUY TẮC BẮT BUỘC:
- PHẢI sử dụng dữ liệu bên dưới
- Nếu user hỏi 1 thành phố → chỉ trả thành phố đó
- Nếu user hỏi chung chung → chọn thành phố hợp lý hoặc tóm tắt
- Không được bịa

User: {username}: {user_message}

Dữ liệu thời tiết:
{json.dumps(tool_result, ensure_ascii=False, indent=2)}

Trả lời như Wyvern (ngắn gọn, tự nhiên).
Hãy trả lời lại như Wyvern (tự nhiên, toxic nhẹ, ngắn gọn).
"""

        return await self.get_model_response(prompt)
