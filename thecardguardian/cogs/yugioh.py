"""TheCardGuardian Yugioh Cog."""

from __future__ import annotations

import datetime

import aiohttp
import discord
from discord.commands import Option
from discord.ext import commands, tasks
from discord.ext.pages import Paginator


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
        self.send_daily_yugioh_card.start()

    async def __get_and_set_random_yugioh_card(self) -> None:
        """Get a random card from the YGOPRODECK API.

        This is a private method and should not be called outside of this class.
        """
        async with aiohttp.ClientSession() as session, session.get(
            "https://db.ygoprodeck.com/api/v7/randomcard.php",
        ) as req:
            if req.status == self.REQ_SUCCESS:
                card = await req.json()
                self.daily_card_name = card["data"][0]["name"]
                self.daily_card_image_uri = card["data"][0]["card_images"][0][
                    "image_url"
                ]
                self.daily_card_type = card["data"][0]["type"]
                self.daily_card_description = card["data"][0]["desc"]
                self.daily_card_prices_usd = card["data"][0]["card_prices"][0][
                    "tcgplayer_price"
                ]

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

    async def __get_named_yugioh_card(self, card_name: str) -> dict | None:
        """Get one or more searched named cards from the YGOPRODECK API.

        This is a private method and should not be called outside of this class.
        """
        async with aiohttp.ClientSession() as session, session.get(
            f"https://db.ygoprodeck.com/api/v7/cardinfo.php?name={card_name}",
        ) as req_exact:
            if req_exact.status == self.REQ_SUCCESS:
                return await req_exact.json()

            async with session.get(
                f"https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={card_name}",
            ) as req_fuzzy:
                if req_fuzzy.status == self.REQ_SUCCESS:
                    return await req_fuzzy.json()

                return None

    async def __get_queried_yugioh_card(self, card_name: str) -> dict | None:
        """Get one or more searched named cards from the YGOPRODECK API.

        This is a private method and should not be called outside of this class.
        """
        async with aiohttp.ClientSession() as session, session.get(
            f"https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={card_name}",
        ) as req:
            if req.status == self.REQ_SUCCESS:
                return await req.json()

            return None

    def __build_card_embed(
        self,
        card: dict,
        data_number: int = 0,
    ) -> discord.Embed:
        """Build card embed with the related card information.

        This is a private method and should not be called outside of this class.
        """
        price = card["data"][data_number]["card_prices"][0]["tcgplayer_price"]

        if price is None:
            price = 0

        embed = discord.Embed(
            title=f"{card["data"][data_number]["name"]}",
            description=f"{card["data"][data_number]["type"]}",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name=f"Price (USD): {price}$",
            value=f"**{card["data"][data_number]["desc"]}**",
            inline=True,
        )
        embed.set_image(
            url=card["data"][data_number]["card_images"][0]["image_url"],
        )
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
                    f"Daily Yu-Gi-Oh! Card Of The Day! {datetime.datetime.now().strftime(self.DATE_FORMAT)}",  # noqa: DTZ005, E501
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

    @discord.slash_command(
        name="yugiohdailyset",
        description="Set this channel to receive TheCardGuardian's Yu-Gi-Oh! card of the day updates",  # noqa: E501
    )
    async def daily_set(self, ctx: discord.ApplicationContext) -> None:
        """Set this channel to receive TheCardGuardian's Yu-Gi-Oh! card of the day updates."""  # noqa: E501
        if self.daily_card_channel_id == ctx.channel_id:
            await ctx.respond(
                f"This channel is already set to receive daily Yu-Gi-Oh! cards everyday at {self.daily_card_hour}:{self.daily_card_minute}.",  # noqa: E501
            )
            return

        if self.daily_card_channel_id is not None:
            await ctx.respond(
                "Another channel is already set to receive Yu-Gi-Oh! daily cards. Please unset that first.",  # noqa: E501
            )

        self.daily_card_channel_id = ctx.channel_id
        await ctx.respond(
            "Yu-Gi-Oh! daily card set to this channel! Type `/yugiohdailytime` to set the time for the Yu-Gi-Oh! daily card to be sent.",  # noqa: E501
        )

    @discord.slash_command(
        name="yugiohdailyunset",
        description="Unset this channel to receive TheCardGuardian's Yu-Gi-Oh! card of the day updates",  # noqa: E501
    )
    async def daily_unset(self, ctx: discord.ApplicationContext) -> None:
        """Unset this channel as the receiver for TheCardGuardian's Yu-Gi-Oh! daily card of the day updates."""  # noqa: E501
        if (
            self.daily_card_channel_id != ctx.channel_id
            or self.daily_card_channel_id is None
        ):
            await ctx.respond(
                "This channel is not set to receive Yu-Gi-Oh! daily cards.",
            )
            return

        self.daily_card_channel_id = None
        await ctx.respond(
            "Daily card unset! Type `/yugiohdailyset` to set this channel to receive the daily Yu-Gi-Oh! card of the day.",  # noqa: E501
        )

    @discord.slash_command(
        name="yugiohdailytime",
        description="Set the time at which the daily Yu-Gi-Oh! card should be sent, in 24 hour format (ex: 17:00)",  # noqa: E501
    )
    async def daily_time(
        self,
        ctx: discord.ApplicationContext,
        time: str = Option(str, "24 hour format (ex: 17:00), use 00:00 for midnight"),
    ) -> None:
        """Set the time at which the daily Yu-Gi-Oh! card should be sent, in 24 hour format (ex: 17:00)."""  # noqa: E501
        if self.daily_card_channel_id is None:
            await ctx.respond(
                "No channel is set to receive daily Yu-Gi-Oh! cards. Please set one first using `/yugiohdailyset`.",  # noqa: E501
            )
            return

        time_split = time.split(":")

        if len(time_split) != self.PROPER_SPLITTED_TIME_LENGTH:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)",
            )
            return

        if int(time_split[0]) > self.MAX_HOUR or int(time_split[1]) > self.MAX_SECOND:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)",
            )
            return

        if int(time_split[0]) < 0 or int(time_split[1]) < 0:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)",
            )
            return

        try:
            self.daily_card_hour = int(time_split[0])
            self.daily_card_minute = int(time_split[1])
        except ValueError:
            await ctx.respond(
                "Invalid time format. Please use 24 hour format (ex: 17:00)",
            )
            return

        await ctx.respond(
            "Daily Yu-Gi-Oh! card time set to "
            + str(time_split[0])
            + ":"
            + str(time_split[1]),
        )

    @discord.slash_command(
        name="yugiohhelp",
        description="Get help with TheCardGuardian Yu-Gi-Oh! commands",
    )
    async def help(self, ctx: discord.ApplicationContext) -> None:
        """Get help with TheCardGuardian Yu-Gi-Oh! commands."""
        embed = discord.Embed(
            title="Help with TheCardGuardian",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="",
            value="""
            To get started with TheCardGuardian, follow the first-time setup instructions listed below:
            1. Create a new channel (or use existing ones!) to receive TheCardGuardian's daily card of the day updates.

            2. Set the channel as the receiver for TheCardGuardian's daily card of the day updates, using `/yugiohdailyset`.

            3. Set the time at which the daily card should be sent, in 24 hour format (ex: 17:00), using `/yugiohdailytime`.

            4. Type `/yugiohdailycard` to receive the daily Magic: The Gathering card of the day, and `/about` to get more information about TheCardGuardian.

            5. Enjoy!
            """,  # noqa: E501
        )
        await ctx.respond(embed=embed)

    @discord.slash_command(
        name="yugiohnamedsearch",
        description="Search for named Yu-Gi-Oh! cards (supports exact and fuzzy search)",  # noqa: E501
    )
    async def named_search(
        self,
        ctx: discord.ApplicationContext,
        query: str = Option(
            str,
            "Enter the name of the Yu-Gi-Oh! card you're searching for",
        ),
    ) -> None:
        """Search for named Yu-Gi-Oh! cards."""
        card = await self.__get_named_yugioh_card(query)
        embeds = []

        if card is None:
            await ctx.respond(f"Query `{query}` is not found.")
            return

        await ctx.respond(f"Returning named search result for query `{query}`")
        embeds.append(self.__build_card_embed(card))

        paginator = Paginator(pages=embeds)
        await paginator.respond(ctx.interaction, ephemeral=True)

    @discord.slash_command(
        name="yugiohquerysearch",
        description="Search for Yu-Gi-Oh! cards by query (supports exact and fuzzy search)",  # noqa: E501
    )
    async def query_search(
        self,
        ctx: discord.ApplicationContext,
        query: str = Option(
            str,
            "Enter the query of the Yu-Gi-Oh! card you're searching for",
        ),
    ) -> None:
        """Search for Yu-Gi-Oh! cards by query."""
        cards = await self.__get_queried_yugioh_card(query)
        embeds = []

        """ if cards["data"] is None:
            await ctx.respond(f"Query `{query}` is not found.")
        return """

        await ctx.respond(f"Returning named search result for query `{query}`")
        for data_number in range(len(cards["data"])):
            embeds.append(self.__build_card_embed(cards, data_number))  # noqa: PERF401

        paginator = Paginator(pages=embeds)
        await paginator.respond(ctx.interaction, ephemeral=True)


def setup(bot: discord.Bot) -> None:
    """Set up the Yugioh cog."""
    bot.add_cog(Yugioh(bot))
