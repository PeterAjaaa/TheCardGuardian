import discord


class TheCardGuardian(discord.Bot):
    async def on_ready(self):
        print(f"{self.user.name} is ready and online!")
        print(f"ID: {self.user.id}")

    async def on_guild_join(self, guild):
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    "Thanks for inviting TheCardGuardian! Type `/magichelp` for Magic: The Gathering and `/ygohelp` for Yu-Gi-Oh! to get started."
                )
