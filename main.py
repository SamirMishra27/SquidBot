import disnake
from disnake.ext import commands

from json import load
from datetime import datetime
from os import environ
from aiohttp import ClientSession

import logging

from utils import CustomContext, CustomVoiceError
logging.basicConfig(level=logging.INFO)

# Setting up variable for jishaku's cog purposes
environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

with open("config.json") as f:
    config = load(f)
    stage = config["STAGE"]

    BOT_TOKEN = config["BOT_TOKEN_" + stage]
    BOT_PREFIX = config["PREFIX_" + stage]

INTENTS = disnake.Intents.all()

def get_prefix(bot, message: disnake.Message):
    bot_id = bot.user.id
    return (f'<@{bot_id}> ', f'<@!{bot_id}> ', BOT_PREFIX, "S.", "s.", "abe", "squid")

class Client(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix = get_prefix,
            case_insensitive = True,
            strip_after_prefix = True,

            intents = INTENTS,
            allowed_mentions = disnake.AllowedMentions(everyone=False, users=True, roles=True, replied_user=True),

            # self_bot = False,
            owner_id = 278094147901194242,
            reload = True,
            max_messages = 50
        )
        self.has_started = False
        self.bot_exts = []

        for ext_name in ("jishaku", "fun", "help", "mod", "owner", "music", "auctions", "events"):
            self.load_extension(ext_name)
            self.bot_exts.append(ext_name)
            print('Loaded ', ext_name)
        
        self.version = "2.0"
        self.debug_channel = 902643527777931355
        self.log = logging.getLogger()
        self.launched_at = None
        self.last_message_cache = {}
        self.session = ClientSession()
        
    async def on_ready(self):
        self.has_started = True
        print(
            "\n\nWe have successfully logged in as {0.user} \n".format(self) +\
            "Disnake version info: {}\n".format(disnake.version_info) +\
            "Disnake version: {}\n".format(disnake.__version__)
        )

    @property
    def prefix(self):
        return BOT_PREFIX

    def run(self, *args, **kwargs):
        self.launched_at = datetime.now()
        super().run(*args, **kwargs)

    async def on_message(self, message):
        if message.content.replace('!', '') == self.user.mention:
            await message.channel.send("My default prefix is `{}`".format(self.prefix))

        elif message.content.startswith("s.hello"):
            await message.channel.send("Hello! :skull:")
        
        return await super().on_message(message)

    async def get_context(self, message):
        return await super().get_context(message, cls = CustomContext)

    async def close(self):
        await self.session.close()
        return await super().close()

    async def on_command_error(self, context, exception):
        if isinstance(exception, CustomVoiceError):
            return await context.send(exception)
        
        if context.author.id == self.owner_id:
            await context.send(exception.__traceback__.__class__)
        return await super().on_command_error(context, exception)

if __name__ == "__main__":
    Client().run(BOT_TOKEN, reconnect = True)