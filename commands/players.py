from discord import app_commands

def setup(tree, bridge):

    @app_commands.command(name="players", description="Get list players ingame")
    async def players(interaction):
        players = bridge.get_players()

        if not players:
            await interaction.response.send_message("No one here 4 sure!")
            return

        msg = f" Players ({len(players)}):\n" + "\n".join(f"• {p}" for p in players)

        await interaction.response.send_message(msg)

    tree.add_command(players)
