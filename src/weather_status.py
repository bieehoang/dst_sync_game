import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta
import discord
import yaml
import os
from github import Github, GithubException

# ====================== LOAD CONFIG ======================
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Do not see config.yaml: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    print(f"[CONFIG] Loaded config.yaml: {config_path}")
    return config

# ====================== CLASS WEATHER ======================
class WeatherStatus:
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.last_warning = {}

        # Load config
        self.config = load_config()

        # Lấy thông tin từ config.yaml
        self.github_token = self.config.get("github", {}).get("token")
        self.repo_name = self.config.get("github", {}).get("repo_name")
        self.discord_channel_id = self.config.get("discord", {}).get("channel_id")
        self.readme_path = "README.md"

        # Lấy danh sách locations từ config
        self.locations = self.config.get("locations", [])
        if not self.locations:
            raise ValueError("Do not see 'locations' in config.yaml")

        print(f"[CONFIG] Loaded {len(self.locations)} locations")

        if not self.github_token or not self.repo_name:
            print("[WARNING] GitHub token or repo_name did not config!")

    async def fetch_weather(self, lat, lon):
        api_key = self.config.get("openweather", {}).get("api_key")
        url = (
            f"https://api.openweathermap.org/data/3.0/onecall"
            f"?lat={lat}&lon={lon}"
            f"&exclude=minutely,daily,alerts"
            f"&appid={api_key}&units=metric"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise Exception(f"OpenWeather API Error: {data.get('message', data)}")

                current = data.get("current")
                hourly = data.get("hourly", [])

                if not current or len(hourly) < 2:
                    raise Exception("Wrong data OPENWEATHER")

                temp = current.get("temp")
                desc = current["weather"][0].get("description", "unknown")
                pop_now = hourly[0].get("pop", 0.0)
                pop_next = hourly[1].get("pop", 0.0)
                rain_now = hourly[0].get("rain", {}).get("1h", 0.0)

                return temp, desc, data["timezone_offset"], pop_now, pop_next, rain_now

    def get_weather_emoji(self, desc):
        desc = desc.lower()
        if "clear" in desc: return "☀️"
        if "cloud" in desc: return "☁️"
        if any(x in desc for x in ["rain", "drizzle"]): return "🌧️"
        if any(x in desc for x in ["storm", "thunder"]): return "⛈️"
        return "🌡️"

    # ================== UPDATE CHỈ 1 DÒNG TRONG README ==================
    async def update_readme(self, weather_lines):
        if not self.github_token or not self.repo_name:
            return

        try:
            g = Github(self.github_token)
            repo = g.get_repo(self.repo_name)
            contents = repo.get_contents(self.readme_path)
            old_content = contents.decoded_content.decode("utf-8")

            # Tạo dòng weather mới
            line_new = "# 🌤️ Weather:"
            for w in weather_lines:
                line_new += f" {w['name']} {w['temp']:.1f}°C | {w['pop_now']}%→{w['pop_next']}% | {w['time']}"

            line_new += f" | Last update: {datetime.now(timezone(timedelta(hours=7))).strftime('%H:%M %d/%m/%Y')}"

            lines = old_content.splitlines()
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith("# 🌤️ Weather:"):
                    lines[i] = line_new
                    updated = True
                    break

            if not updated:
                lines.append("")
                lines.append(line_new)

            new_content = "\n".join(lines)

            repo.update_file(
                path=self.readme_path,
                message=f"♻️ Update weather - {datetime.now().strftime('%H:%M')}",
                content=new_content,
                sha=contents.sha
            )
            print("[GITHUB] Update README.md")

        except Exception as e:
            print(f"[GITHUB ERROR] {e}")
    async def get_all_weather_data(self):
        results = []
        api_key = self.config.get("openweather", {}).get("api_key")

        for loc in self.locations:
            try:
                temp, desc, offset, pop_now, pop_next, rain_now = await self.fetch_weather(loc["lat"], loc["lon"])

                local_time = (datetime.now(timezone.utc) + timedelta(seconds=offset)).strftime("%H:%M")
                emoji = self.get_weather_emoji(desc)
                temp_f = temp * 9/5 + 32

                rain_percent_now = int(pop_now * 100)
                rain_percent_next = int(pop_next * 100)

                results.append({
                    "name": loc["name"],
                    "emoji": emoji,
                    "temp": temp,
                    "temp_f": temp_f,
                    "pop_now": rain_percent_now,
                    "pop_next": rain_percent_next,
                    "local_time": local_time,
                    "desc": desc
                })

            except Exception as e:
                print(f"[WEATHER FETCH ERROR] {loc['name']}: {e}")
                results.append({
                    "name": loc["name"],
                    "emoji": "❌",
                    "temp": None,
                    "pop_now": None,
                    "pop_next": None,
                    "local_time": "Error",
                    "desc": "Fetch error"
                })

        return results
    # ================== MAIN LOOP ==================
    async def update_status_loop(self):
        await self.bot.wait_until_ready()
        weather_data = []

        while not self.bot.is_closed():
            loc = self.locations[self.index]
            location_name = loc["name"]

            try:
                temp, desc, offset, pop_now, pop_next, rain_now = await self.fetch_weather(loc["lat"], loc["lon"])

                local_time = (datetime.now(timezone.utc) + timedelta(seconds=offset)).strftime("%H:%M")
                emoji = self.get_weather_emoji(desc)
                temp_f = temp * 9/5 + 32

                rain_percent_now = int(pop_now * 100)
                rain_percent_next = int(pop_next * 100)

                # Cảnh báo sắp mưa
                if rain_percent_next >= 60 and not self.last_warning.get(location_name, False):
                    channel = self.bot.get_channel(self.discord_channel_id)
                    if channel:
                        await channel.send(
                            f" **{location_name}**\n"
                            f"> **{rain_percent_next}%**Seems willbe raining outside, keep dry mate!\n"
                            f"> {local_time} | {temp:.1f}°C"
                        )
                    self.last_warning[location_name] = True
                elif rain_percent_next < 40:
                    self.last_warning[location_name] = False

                # Update Discord status
                status_text = f"> {local_time} | {emoji} {location_name} {temp:.1f}°C/ {temp_f:.1f}°F\n> Rain POP: {rain_percent_now}% → 1hr next: {rain_percent_next}%"
                await self.bot.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.custom, name="Weather", state=status_text[:128])
                )

                channel = self.bot.get_channel(self.discord_channel_id)
                if channel:
                    await channel.send(f"**Weather Update**:\n{status_text}")

                weather_data.append({
                    'name': location_name,
                    'time': local_time,
                    'temp': temp,
                    'pop_now': rain_percent_now,
                    'pop_next': rain_percent_next
                })
                await self.update_readme(weather_data)
                print(f"[WEATHER] {location_name} | {local_time} | {temp:.1f}°C | {rain_percent_now}% → {rain_percent_next}%")

            except Exception as e:
                print(f"[WEATHER ERROR] {location_name}: {e}")
             

            self.index = (self.index + 1) % len(self.locations)
            await asyncio.sleep(1800)  # 30 phút
