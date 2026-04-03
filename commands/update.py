import discord
from discord import app_commands
import asyncio
from src.logger import logger

async def setup(tree: discord.app_commands.CommandTree, bridge):
    @tree.command(name="update", description="Update Wyvern DST Server")
    @app_commands.checks.has_role(1385632574470226081)
    async def update_server(interaction: discord.Interaction):
        await interaction.response.send_message("Updating Wyvern DST Server")

        try:
            process = await asyncio.create_subprocess_shell(
                "/home/steam/server_dst/bin/dst_manager.sh update",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/steam/server_dst/bin"
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=700)
            except asyncio.TimeoutError:
                await interaction.followup.send("502!")
                try:
                    process.kill()
                except:
                    pass
                logger.error("Update command timed out")
                return

            if process.returncode == 0:
                await interaction.followup.send("Updated Wyvern DST Server n Restarted")
                if bridge:
                    await bridge.send_to_discord("Server", "Updated Wyvern DST Server n Restarted")
                logger.info("Update command executed successfully")
            else:
                # Fix lấy lỗi an toàn hơn
                error_msg = ""
                if stderr:
                    error_msg = stderr.decode(errors='ignore').strip()[:800]
                if not error_msg:
                    error_msg = f"Process exited with code {process.returncode}"

                await interaction.followup.send(f"Update Failed!\nError: {error_msg}")
                logger.error(f"Update error: {error_msg}")

        except asyncio.TimeoutError:
            await interaction.followup.send("502!")
            logger.error("Update command timed out")
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")
            logger.error(f"Update command exception: {e}")
