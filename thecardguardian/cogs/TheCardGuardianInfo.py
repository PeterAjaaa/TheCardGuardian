import discord
from discord.ext import commands


class TheCardGuardianInfo(commands.Cog):
    @discord.slash_command(
        name="about",
        description="About TheCardGuardian",
    )
    async def about(self, ctx: discord.ApplicationContext):
        """
        Parameter: discord.ApplicationContext
        Return Type: None
        Description:
        Send a message with information about the bot.
        """
        embed = discord.Embed(
            title="About TheCardGuardian",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="",
            value="""
            TheCardGuardian is a Discord Bot for MTG and YuGiOh! Trading Card Game.

            TheCardGuardian is open-source and available on GitHub

            TheCardGuardian is not affiliated with Scryfall or YGOPRODeck or Magic: The Gathering or Yu-Gi-Oh!.

            All rights goes to their respective owners.

            **Source Code**
            [GitHub](https://github.com/PeterAjaaa/TheCardGuardian)
            """,
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(TheCardGuardianInfo(bot))
