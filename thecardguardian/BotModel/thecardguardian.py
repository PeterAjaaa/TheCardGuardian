"""Bot model for TheCardGuardian."""

import discord


class TheCardGuardian(discord.Bot):
    """TheCardGuardian Bot."""

    async def on_ready(self) -> None:
        """Define what happens when the bot is ready.

        Parameter: None
        Return Type: None
        """
        print(f"{self.user.name} is ready and online!")  # noqa: T201
        print(f"ID: {self.user.id}")  # noqa: T201

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Define what happens when the bot joins a guild.

        Parameter: discord.Guild
        Return Type: None
        """
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    "Thanks for inviting TheCardGuardian! Type `/magichelp` for Magic: The Gathering and `/ygohelp` for Yu-Gi-Oh! or `/digimonhelp` for Digimon TCG to get started.",  # noqa: E501
                )
