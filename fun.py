from disnake import (
    ApplicationCommandInteraction, 
    PCMVolumeTransformer, 
    FFmpegPCMAudio,
    ButtonStyle,
    Member,
    Message
)
from disnake.ext import commands
from disnake.ui import View, button

from utils import CustomVoiceError, CustomVoiceError

from asyncio import sleep
from os import remove, path
from wavelink import Player, WaitQueue
from utils import CustomContext
from time import time
from re import sub

import gtts

class ReplyButtonView(View):
    def __init__(self, text, author, target_user, reply_message):
        super().__init__(timeout = None)
        self.text = text
        self.author = author
        self.target_user = target_user
        self.reply_message = reply_message

    async def interaction_check(self, interaction):
        if interaction.user.id == self.target_user.id:
            return True
        await interaction.response.send_message("This reply is not for you! 👎", ephemeral = True)
        return False

    @button(style = ButtonStyle.blurple, label = "Click to see! 📥", disabled = False)
    async def show_reply(self, button, interaction):

        content = "{} said this to you.\n> {}\n\n".format(self.author.mention, self.text)
        if self.reply_message != None:
            content += "**They replied to this message:** \n>>> {}".format(self.reply_message.content)
        await interaction.response.send_message(content = content, ephemeral = True)

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_people = {}

    @commands.command()
    async def ping(self, ctx):
        resp = await ctx.send("Pinging...")
        diff = resp.created_at - ctx.message.created_at
        return await resp.edit(
            content = f"Pong! latency -> {int(self.bot.latency * 1000)} ms! \nRoundtrip -> {1000*diff.total_seconds()}ms!"
        )

    @commands.command()
    async def gtts(self, ctx, accent: str = "com", *, text: str):
        # TO DO: add a queue system

        if len(text) > 500:
            raise CustomVoiceError("Keep the length of text below 500 ok?")

        # Check for accent first
        accents = ["com.au", "co.uk", "com", "ca", "co.in", "ie", "co.za"]

        if accent not in accents:
            final_text = str(accent) + ' ' + text
            accent = "com"
        else:
          final_text = text

        # Now process the voice
        filename = "temporary/{}.mp3".format(ctx.author.id)
        tts = gtts.gTTS(final_text, lang = "en", tld = accent) 
        tts.save(filename)
        
        audio = PCMVolumeTransformer(FFmpegPCMAudio(filename))
        while True:
            if ctx.voice_client.is_playing():
                await sleep(1)
                continue
            else: break
        ctx.voice_client.play(audio, after = lambda e: print(f"Player error: {e}") if e else None)

        if not isinstance(ctx, ApplicationCommandInteraction):
            await ctx.react("✅")

        while True:
            if ctx.voice_client.is_playing():
                await sleep(1)
                continue
            else: break

        await sleep(0.5)
        self.bot.log.info("filesize: {}".format(path.getsize(filename)))

        # 19968 bytes equals roughly over 20kb.
        remove("temporary/{}.mp3".format(ctx.author.id))

    @gtts.before_invoke
    async def ensure_voice_is_connected(self, ctx):
        if ctx.voice_client is None or not ctx.guild.me.voice:

            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                ctx.voice_client.text_channel = ctx.channel
                ctx.voice_client.queue = WaitQueue()

            else:
                raise CustomVoiceError("Join a voice channel first dumbass. 🎙️")

        else:
            if isinstance(ctx.voice_client, Player):
                raise CustomVoiceError("I am currently playing music, make me leave the channel and then run the command again.")

    @commands.command(
        name = 'task',
        usage = "s. task [time gap] [command name]"
    )
    async def task(self, ctx, time_gap: str, *, command: str):
        types = {'s': '1', 'm': '60', 'h': '3600', 'd': '86400', 'w': '604800'}

        for word in time_gap:
            if word.lower() in types:
                time_gap = time_gap.replace(word, "*" + types[word] + "+")
                # 2h -> 2*3600 -> int()
        time_gap = time_gap.rstrip("+")
        try:
            time_gap = eval(time_gap)
        except Exception as e:
            return await ctx.send("Invalid time specified!")

        await ctx.send(
            f"Every time you run `{command}` command, i will remind you to do it again after {time_gap} seconds.\n"
            f"It times out after waiting for a response for max 1 hour. (Max loops 24 times)"
        )

        check = lambda x: x.author == ctx.author and x.channel == ctx.channel and x.content.lower() == command.lower()
        for i in range(24):
            try:
                await self.bot.wait_for('message', timeout = 3600, check = check)
            except:
                return
            await sleep(time_gap)
            await ctx.send(f"{ctx.author.mention} it's time to run your {command} command again!")

    @commands.slash_command(
        name = "reply",
        description = "This lets you send a private reply right in the channel without having to go into the person's DM."
    )
    async def reply(
        ctx,
        text: str = commands.Param(name = "text"),
        target_user: Member = commands.Param(name = "person"),
        reply_message_id: str = commands.Param(default = "None", name = "reply_message_id", min_value = 17, max_value = 19)
    ):
        target_user
        if not reply_message_id == "None":
            reply_message = await ctx.channel.fetch_message(reply_message_id)
        else:
            reply_message = None
        view = ReplyButtonView(text, ctx.user, target_user, reply_message)

        await ctx.channel.send(
            "{}, someone has a privately replied to you!".format(target_user.mention), 
            view = view
        )
        await ctx.send("Reply successfully sent!", ephemeral = True)
        print(ctx.author, text)

    @commands.command(name = "afk")
    async def away_from_keyboard(self, ctx: CustomContext, message: str = ""):
        
        message = sub(r"<@!?([0-9]+)>", "", message)

        self.afk_people.update(
            {ctx.author.id: [time(), message, ctx.message.id]}
        )
        await ctx.send("{}, I set your AFK, see you later!".format(ctx.author.mention))

    @commands.Cog.listener("on_message")
    async def on_message(self, message: Message):

        if message.author.bot:
            return
        
        if message.author.id in self.afk_people:
            if message.id != self.afk_people[message.author.id][2]:
                self.afk_people.pop(message.author.id)
                await message.channel.send("Welcome back **{}**, I removed your AFK!".format(message.author.name))

        for mention in message.raw_mentions:
            if mention in self.afk_people:

                user = await self.bot.get_or_fetch_user(mention)
                time_since = f"<t:{ int(self.afk_people[mention][0]) }:R>"
                afk_message = self.afk_people[mention][1]

                await message.channel.send("{} is AFK since {}! Message: {}".format(user.name, time_since, afk_message or "Nothing"))
                break

def setup(bot):
    bot.add_cog(Fun(bot))