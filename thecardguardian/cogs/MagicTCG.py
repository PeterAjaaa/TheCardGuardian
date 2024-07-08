import datetime

import aiohttp
import discord
from discord.ext import commands, tasks

# TODO: Set up a database and cache the images (and maybe the responses?), so that we don't hit the limit rate of the API
# NOTE: YGOPRODeck requires us to download and re-host the images ourselves. Might as well do this for Scryfall API too.


class MagicTCG(commands.Cog):
    daily_card_name = None
    daily_card_image_uri = None
    daily_card_type = None
    daily_card_description = None

    daily_card_channel_id = None
    daily_card_hour = None
    daily_card_minute = None
    first_run = True

    DATE_FORMAT = "%d %B %Y"

    def __init__(self, bot):
        self.bot = bot
        self.send_daily_magic_card.start()

    async def __get_random_magic_card(self):
        """
        Parameter: None
        Return Type: None
        Description:
        Get a random card from the Scryfall API.
        This is a private method and should not be called outside of this class.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.scryfall.com/cards/random") as req:
                if req.status == 200:
                    self.card = await req.json()
                    self.daily_card_name = self.card["name"]
                    self.daily_card_image_uri = self.card["image_uris"]["png"]
                    self.daily_card_type = self.card["type_line"]
                    self.daily_card_description = self.card["oracle_text"]

    def __build_daily_embed(self):
        """
        Parameter: None
        Return Type: discord.Embed
        Description:
        Build an embed with the card information.
        This is a private method and should not be called outside of this class.
        """
        embed = discord.Embed(
            title=self.daily_card_name,
            description=f"**{self.daily_card_type}**",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="", value=f"**{self.daily_card_description}**")
        embed.set_image(url=self.daily_card_image_uri)
        embed.set_footer(
            text="TheCardGuardian\nTheCardGuardian is not affiliated with Scryfall or YGOPRODeck or Magic: The Gathering or Yu-Gi-Oh!\nAll rights goes to their respective owners."
        )
        return embed

    @tasks.loop(seconds=1)
    async def send_daily_magic_card(self):
        """
        Parameter: None
        Return Type: None
        Description:
        Send the daily card of the day to the channel.
        """
        if (
            self.daily_card_hour is not None
            and self.daily_card_minute is not None
            and self.daily_card_channel_id is not None
        ):
            now = datetime.datetime.now().time()
            target_time = datetime.time(
                hour=self.daily_card_hour, minute=self.daily_card_minute, second=0
            )
            print(now, target_time)
            if (
                now.hour == target_time.hour
                and now.minute == target_time.minute
                and now.second == target_time.second
            ):
                channel = self.bot.get_channel(self.daily_card_channel_id)
                await self.__get_random_magic_card()
                await channel.send(
                    f"Daily Card Of The Day! {datetime.date.today().strftime(self.DATE_FORMAT)}",
                    embed=self.__build_daily_embed(),
                )
                self.first_run = False

    @discord.slash_command(
        name="magicdailycard",
        description="Get the daily Magic card of the day",
    )
    async def get_daily_magic_card(self, ctx: discord.ApplicationContext):
        """
        Parameter: discord.ApplicationContext
        Return Type: None
        Description:
        Get the daily card of the day.
        The condition basically checks whether the daily card has been sent before.
        If it's the first run, it acts both as a getter and a setter both at the same time.
        """
        if self.first_run is True:
            await self.__get_random_magic_card()
            self.first_run = False

        await ctx.respond(
            f"Daily Card Of The Day! {datetime.date.today().strftime(self.DATE_FORMAT)}",
            embed=self.__build_daily_embed(),
        )

    @discord.slash_command(
        name="magicdailyset",
        description="Set this channel to receive TheCardGuardian's card of the day updates",
    )
    async def daily_set(self, ctx: discord.ApplicationContext):
        """
        Parameter: discord.ApplicationContext
        Return Type: None
        Description:
        Set this channel to receive TheCardGuardian's card of the day updates.
        """
        if self.daily_card_channel_id == ctx.channel_id:
            await ctx.respond(
                f"This channel is already set to receive daily Magic cards everyday at {self.daily_card_hour}:{self.daily_card_minute}."
            )
            return

        if self.daily_card_channel_id is not None:
            await ctx.respond(
                "Another channel is already set to receive daily cards. Please unset that first."
            )

        self.daily_card_channel_id = ctx.channel_id
        await ctx.respond(
            "Daily card set to this channel! Type `/magicdailytime` to set the time for the daily card to be sent."
        )

    @discord.slash_command(
        name="magicdailyunset",
        description="Unset this channel to receive TheCardGuardian's card of the day updates",
    )
    async def daily_unset(self, ctx: discord.ApplicationContext):
        """
        Parameter: discord.ApplicationContext
        Return Type: None
        Description:
        Unset this channel as the receiver for TheCardGuardian's daily card of the day updates.
        """
        if (
            self.daily_card_channel_id != ctx.channel_id
            or self.daily_card_channel_id is None
        ):
            await ctx.respond("This channel is not set to receive daily cards.")
            return

        self.daily_card_channel_id = None
        await ctx.respond(
            "Daily card unset! Type `/magicdailyset` to set this channel to receive the daily card of the day."
        )

    @discord.slash_command(
        name="magicdailytime",
        description="Set the time at which the daily card should be sent, in 24 hour format (ex: 17:00)",
    )
    async def daily_time(self, ctx: discord.ApplicationContext, time: str):
        """
        Parameter: discord.ApplicationContext
        Return Type: None
        Description:
        Set the time at which the daily card should be sent, in 24 hour format (ex: 17:00).
        """
        time_split = time.split(":")

        if len(time_split) != 2:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)"
            )
            return

        if int(time_split[0]) > 23 or int(time_split[1]) > 59:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)"
            )
            return

        if int(time_split[0]) < 0 or int(time_split[1]) < 0:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)"
            )
            return

        try:
            self.daily_card_hour = int(time_split[0])
            self.daily_card_minute = int(time_split[1])
        except ValueError:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)"
            )
            return

        await ctx.respond(
            "Daily card time set to " + str(time_split[0]) + ":" + str(time_split[1])
        )

    @discord.slash_command(
        name="magichelp", description="Get help with TheCardGuardian Magic commands"
    )
    async def help(self, ctx: discord.ApplicationContext):
        """
        Parameter: discord.ApplicationContext
        Return Type: None
        Description:
        Get help with TheCardGuardian Magic commands.
        """
        embed = discord.Embed(
            title="Help with TheCardGuardian",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="",
            value="""
            To get started with TheCardGuardian, follow the first-time setup instructions listed below:
            1. Create a new channel (or use existing ones!) to receive TheCardGuardian's daily card of the day updates.

            2. Set the channel as the receiver for TheCardGuardian's daily card of the day updates, using `/magicdailyset`.

            3. Set the time at which the daily card should be sent, in 24 hour format (ex: 17:00), using `/magicdailytime`.

            4. Type `/magicdailycard` to receive the daily card of the day, and `/about` to get more information about TheCardGuardian.

            5. Enjoy!
            """,
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(MagicTCG(bot))
