"""TheCardGuardian Yugioh Cog."""

import datetime

import aiohttp
import discord
from discord.ext import commands, tasks


class Yugioh(commands.Cog):
    """TheCardGuardian Yugioh Cog."""

    daily_card_name = None
    daily_card_image_uri = None
    daily_card_type = None
    daily_card_description = None

    daily_card_prices_usd = None
    daily_card_channel_id = None
    daily_card_hour = None
    daily_card_minute = None

    first_run = True

    DATE_FORMAT = "%d %B %Y"
    REQ_SUCCESS = 200
    EMBED_FOOTER = "TheCardGuardian\nTheCardGuardian is not affiliated with Scryfall or YGOPRODeck or DigimonCard.io or Magic: The Gathering or Yu-Gi-Oh! or Digimon Card Game.\nAll rights goes to their respective owners."  # noqa: E501
    REQ_NOT_FOUND = 404
    PROPER_SPLITTED_TIME_LENGTH = 2
    MAX_HOUR = 23
    MAX_SECOND = 59

    def __init__(self, bot: discord.Bot) -> None:
        """Initialize the Yugioh cog."""
        self.bot = bot

    async def __get_and_set_random_yugioh_card(self) -> None:
        """Get a random card from the YGOPRODECK API.

        This is a private method and should not be called outside of this class.
        """
        async with aiohttp.ClientSession() as session, session.get(
            "https://db.ygoprodeck.com/api/v7/randomcard.php",
        ) as req:
            if req.status == self.REQ_SUCCESS:
                card = await req.json()
                self.daily_card_name = card["name"]
                self.daily_card_image_uri = card["card_images"][0]["image_url"]
                self.daily_card_type = card["type"]
                self.daily_card_description = card["desc"]
                self.daily_card_prices_usd = card["card_prices"][0]["tcgplayer_price"]

    def __build_daily_embed(self) -> None:
        """Build an embed with the card information.

        This is a private method and should not be called outside of this class.
        """
        if self.daily_card_prices_usd is None:
            self.daily_card_prices_usd = 0

        embed = discord.Embed(
            title=self.daily_card_name,
            description=f"**{self.daily_card_type}**",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name=f"Price (USD): {self.daily_card_prices_usd}$",
            value=f"**{self.daily_card_description}**",
        )
        embed.set_image(url=self.daily_card_image_uri)
        embed.set_footer(text=self.EMBED_FOOTER)
        return embed

    @tasks.loop(seconds=1)
    async def send_daily_yugioh_card(self) -> None:
        """Send the daily card of the day to the channel."""
        if (
            self.daily_card_hour is not None
            and self.daily_card_minute is not None
            and self.daily_card_channel_id is not None
        ):
            now = datetime.datetime.now().time()  # noqa: DTZ005
            target_time = datetime.time(
                hour=self.daily_card_hour,
                minute=self.daily_card_minute,
                second=0,
            )
            if (
                now.hour == target_time.hour
                and now.minute == target_time.minute
                and now.second == target_time.second
            ):
                channel = self.bot.get_channel(self.daily_card_channel_id)
                await self.__get_and_set_random_yugioh_card()
                await channel.send(
                    f"Yu-Gi-Oh! Daily Card Of The Day! {datetime.datetime.now().strftime(self.DATE_FORMAT)}",  # noqa: DTZ005, E501
                    embed=self.__build_daily_embed(),
                )
                self.first_run = False

    @discord.slash_command(
        name="yugiohdailycard",
        description="Get the daily Yugioh card of the day",
    )
    async def get_daily_yugioh_card(self, ctx: discord.ApplicationContext) -> None:
        """Get the daily card of the day.

        The condition basically checks whether the daily card has been sent before.
        If it's the first run, it acts both as getter and setter both at the same time
        """
        if self.first_run is True:
            await self.__get_and_set_random_yugioh_card()
            self.first_run = False

        await ctx.respond(
            f"Daily Card Of The Day! {datetime.date.today().strftime(self.DATE_FORMAT)}",  # noqa: DTZ011, E501
            embed=self.__build_daily_embed(),
        )


def setup(bot: discord.Bot) -> None:
    """Set up the Yugioh cog."""
    bot.add_cog(Yugioh(bot))
