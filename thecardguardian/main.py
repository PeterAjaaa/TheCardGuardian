"""Main calling code for running TheCardGuardian."""

import os

from BotModel.thecardguardian import TheCardGuardian
from dotenv import load_dotenv

load_dotenv()
bot = TheCardGuardian()
bot.load_extension("cogs.MagicTCG")
bot.load_extension("cogs.TheCardGuardianInfo")

bot.run(os.getenv("TOKEN"))
