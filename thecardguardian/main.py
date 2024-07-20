"""Main calling code for running TheCardGuardian."""

import os

from BotModel.thecardguardian import TheCardGuardian
from dotenv import load_dotenv

load_dotenv()
bot = TheCardGuardian()
bot.load_extension("cogs.magic_tcg")
bot.load_extension("cogs.thecardguardian_info")

bot.run(os.getenv("TOKEN"))
