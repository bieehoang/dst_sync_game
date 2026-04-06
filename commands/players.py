from discord import app_commands
from src.bridge import Bridge
from src.logger import logger


def setup(tree, bridge: Bridge):
    """
    Setup the /players slash command.
    """

    @app_commands.command(
        name="players",
        description="Get list of players currently"
    )
    async def players(interaction):
        """
        Handler for the /players command.
        """
        players_dict = bridge.get_players()

        if not players_dict:
            await interaction.response.send_message("No one here 4 sure!")
            return

        lines = []
        for name, user_id in players_dict.items():
            lines.append(f"• {name} - `{user_id}`")

        msg = f"**Players Online ({len(players_dict)})**:\n" + "\n".join(lines)

        await interaction.response.send_message(msg)
        logger.info(f"[PLAYERS] {interaction.user} requested player list - {len(players_dict)} players")

    tree.add_command(players)
