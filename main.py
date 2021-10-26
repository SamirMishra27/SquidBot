from discord.ext import commands
from json import load
from datetime import datetime
from os import environ

import logging
import discord

with open("config.json") as f:
    logging.basicConfig(level=logging.INFO)
    config = load(f)
    BOT_TOKEN = config["BOT_TOKEN"]
    BOT_PREFIX = config["PREFIX"]

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = BOT_PREFIX,
            case_insensitive = True,
            intents = discord.Intents.all(),
            self_bot = False,
            allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=True),
            strip_after_prefix = True
        )
        self.load_extension("jishaku")
        self.version = "1.0"
        self.debug_channel = 0
        self.log = logging.getLogger()
        self.launched_at = None

    def run(self, *args, **kwargs):
        self.launched_at = datetime.now()
        super().run(*args, **kwargs)

    @property
    def prefix(self):
        return BOT_PREFIX

    async def on_ready(self):
        print("\n\nWe have successfully logged in as {0.user} \n".format(self) +\
                "Pycord Alpha version info: {}\n".format(discord.version_info) +\
                "Pycord Alpha version: {}\n".format(discord.__version__))

    async def on_message(self, message):
        if message.content.replace('!', '') == self.user.mention:
            await message.channel.send("My default prefix is `{}`".format(self.prefix))

        elif message.content.startswith("s.hello"):
            await message.channel.send("Hello! :skull:")

        return await super().on_message(message)

    async def close(self):
        return await super().close()

if __name__ == "__main__":
    environ["JISHAKU_NO_UNDERSCORE"] = "True"
    environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
    Client().run(BOT_TOKEN, reconnect = True)