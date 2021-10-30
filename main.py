from discord.ext import commands
from json import load
from datetime import datetime
from os import environ

from discord.commands import slash_command, Option
from views import ReplyButtonView, laptop_json

import logging
import discord

# Setting up variable for jishaku's cog purposes
environ["JISHAKU_NO_UNDERSCORE"] = "True"
environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

with open("config.json") as f:
    logging.basicConfig(level=logging.INFO)
    config = load(f)
    BOT_TOKEN = config["BOT_TOKEN"]
    BOT_PREFIX = config["PREFIX"]

def get_prefix(bot, message: discord.Message):
    bot_id = bot.user.id
    return (f'<@{bot_id}> ', f'<@!{bot_id}> ', BOT_PREFIX, "S.")

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = get_prefix,
            case_insensitive = True,
            intents = discord.Intents.all(),
            self_bot = False,
            allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=True),
            strip_after_prefix = True
        )
        self.has_started = False
        for ext_name in ("jishaku", "fun", "events", "owner", "music"):
            self.load_extension(ext_name)
        
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
        self.has_started = True
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

# Initiate Client object here
Client = Client()

@Client.slash_command(guild_ids = [902643456260841553])
async def reply(
    ctx,
    body: Option(str, description = "Reply text", required = True),
    target: Option(discord.Member, description = "Whom are you replying to? tag them", required = True),
    reply_message_id: Option(str, description = "The ID of the message you are replying in respect of, this one is optional", required = False)
):
    text = body
    target_user = target
    reply_message = await ctx.channel.fetch_message(reply_message_id)
    view = ReplyButtonView(text, ctx.user, target_user, reply_message)

    await ctx.channel.send(
        "{}, someone has a privately replied to you!".format(target_user.mention), 
        view = view
    )
    await ctx.respond("Reply successfully sent!", ephemeral = True)

# This is a test slash command
@Client.slash_command(guild_ids = [902643456260841553])
async def laptop(ctx, option = Option(str)):
    await ctx.respond("Result: {}".format(ctx.message))

if __name__ == "__main__":
    Client.run(BOT_TOKEN, reconnect = True)