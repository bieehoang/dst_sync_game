import discord
from discord import app_commands
from datetime import datetime

# Import class WeatherStatus từ src
from src.weather_status import WeatherStatus

def setup(tree, bot):

    # Tạo instance để dùng hàm chung
    weather_instance = WeatherStatus(bot)

    @app_commands.command(name="weather", description="weather logs")
    async def weather_command(interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            data = await weather_instance.get_all_weather_data()

            lines = []
            for w in data:
                if w["temp"] is None:
                    lines.append(f"• {w['emoji']} **{w['name']}**: Fetch data fail")
                    continue

                lines.append(
                    f"{w['emoji']} **{w['name']}**\n"
                    f"• Temp: **{w['temp']}°C** / {w['temp_f']}°F\n"
                    f"• Time: {w['local_time']}\n"
                    f"• Rain POP: **{w['pop_now']}%** | Next hr: **{w['pop_next']}%**"
                )

            embed = discord.Embed(
                title="Weather Status",
                description="\n\n".join(lines),
                color=0x00ffcc
            )
            embed.set_footer(text=f"Last updated: {datetime.now().strftime('%H:%M %d/%m/%Y')}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Fetch data fail: {e}")

    tree.add_command(weather_command)
