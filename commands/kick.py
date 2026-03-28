import discord
from discord import app_commands
from src.bridge import Bridge
from src.logger import logger


def setup(tree, bridge: Bridge):
    """
    Setup the /kick slash command.
    """

    @app_commands.command(
        name="kick",
        description="Kick a player from the DST server using SteamID64 or KU_ID"
    )
    @app_commands.describe(
        player_id="SteamID64 or KU_ID of the player you want to kick"
    )
    @app_commands.checks.has_any_role(
        1385632295498678312,
        1385907308235718656,
        1385632574470226081
    )
    async def kick_command(interaction: discord.Interaction, player_id: str):
        """
        Handler for the /kick command.
        """
        await interaction.response.defer(ephemeral=False)

        if not bridge:
            await interaction.followup.send("Bridge is not ready!", ephemeral=False)
            return

        # Clean player ID
        player_id = player_id.strip()

        # Execute kick
        success = bridge.kick_command(player_id)

        if success:
            embed = discord.Embed(
                title="Kick Command Sent",
                description="The kick command has been sent to the server.",
                color=0x00ff00
            )
            embed.add_field(name="Player ID", value=f"`{player_id}`", inline=False)
            embed.add_field(
                name="Console Command", 
                inline=False
            )
            embed.set_footer(text=f"Executed by: {interaction.user}")

            await interaction.followup.send(embed=embed, ephemeral=False)
            logger.info(f"[KICK] {interaction.user} kicked player: {player_id}")
        else:
            await interaction.followup.send(
                f"Failed to execute kick command for ID: `{player_id}`\n"
                f"<@1005125632176443492> - 911",
                ephemeral=True
            )

    tree.add_command(kick_command)
    print("[COMMAND] /kick command has been loaded successfully")
