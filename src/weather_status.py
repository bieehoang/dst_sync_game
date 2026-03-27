import aiohttp
import asyncio
from datetime import datetime
import pytz
import discord

LOCATIONS = [
    {"name": "Ho Chi Minh", "lat": 10.8231, "lon": 106.6297, "tz": "Asia/Ho_Chi_Minh"},
    {"name": "Florida", "lat": 27.9944, "lon": -81.7603, "tz": "America/New_York"},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"},
]

API_KEY = "2ef1f02e0355a20f82921f21f84a3146"


class WeatherStatus:
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.last_rain_state = {}
    async def fetch_weather(self, lat, lon):
        url = (
            f"https://api.openweathermap.org/data/3.0/onecall"
            f"?lat={lat}&lon={lon}"
            f"&exclude=minutely,hourly,daily,alerts"
            f"&appid={API_KEY}&units=metric"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                print(data)
                if resp.status != 200:
                    raise Exception(data)

                current = data.get("current")
                if not current:
                    raise Exception(f"Invalid data: {data}")

                temp = current.get("temp")
                desc = current.get("weather", [{}])[0].get("description", "unknown")
                rain_chance = data.get("hourly", [{}])[0].get("pop", 0) 
                weather = data["current"]["weather"][0]
                weather_id = weather["id"] 
                return temp, desc, data["timezone_offset"], rain_chance, weather_id
    def get_weather_emoji(self, desc):
        desc = desc.lower()
        if "clear" in desc:
            return "☀️"
        if "cloud" in desc:
            return "☁️"
        if "rain" in desc:
            return "🌧️"
        if "storm" in desc:
            return "⛈️"
        return "🌡️"
    def is_raining(self, desc):
        desc = desc.lower()
        return any(word in desc for word in ["rain", "storm", "drizzle", "thunder"])
    async def update_status_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            loc = LOCATIONS[self.index]

            try:
                temp, desc, offset, rain_chance,weather_id = await self.fetch_weather(loc["lat"], loc["lon"])
                from datetime import datetime, timezone, timedelta
                utc_now = datetime.now(timezone.utc)
                local_time = (utc_now + timedelta(seconds=offset)).strftime("%H:%M") 
                emoji = self.get_weather_emoji(desc)
                temp_f = temp * 9/5 + 32
                rain_percent = int(rain_chance * 100)
                is_rain = 200 <= weather_id < 600 
                location_name = loc["name"]
                last_state = self.last_rain_state.get(location_name)

                if last_state != is_rain:
                    self.last_rain_state[location_name] = is_rain

                    channel_id = self.bot.config.data["discord"]["channel_id"]
                    channel = self.bot.get_channel(channel_id)

                    if channel:
                        if is_rain:
                            await channel.send(f"{location_name} raining outsite, keep dry mate!")
                        else:
                            pass 
                status_text = (
                    f"> {local_time} | {emoji} {loc['name']} {temp:.1f}°C/{temp_f:.1f}°F \n "
                    f"> Rain POP: Updating"
                ) 
                await self.bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.custom,
                        name="Weather",
                        state=status_text
                        )
                )

                print(f"[WEATHER] {status_text}")
                channel_id = self.bot.config.data["discord"]["channel_id"]
                channel = self.bot.get_channel(channel_id)

                if channel:
                    await channel.send(f" Weather Update:\n{status_text}")
            
            except Exception as e:
                print(f"[WEATHER ERROR] {e}")

            # rotate location
            self.index = (self.index + 1) % len(LOCATIONS)

            await asyncio.sleep(1800)  
