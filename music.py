from discord.ext import commands

import discord
import asyncio
import youtube_dl

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume = 0.5): 
        super().__init__(source, volume)

        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop = None, stream = False):
        loop = loop or asyncio.get_event_loop()

        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download = not stream)
        )

        if "entries" in data:
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data = data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
        return await ctx.send("Joined {} channel!".format(channel.mention))

    @commands.command()
    async def yt(self, ctx, *, url):
        # WARNING: This command downloads Youtube audio in the current directory, do not run this command.
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(
                player, after = lambda e: print(f"Player error: {e}") if e else None
            )
        await ctx.send("Now playing: {}".format(player.title))

    @commands.command()
    async def play(self, ctx, *, query):
        # Don't run this command either, this command plays music from your local computer
        # so its useless and yes based on my experiments the quality of music was still 
        # the same with pre-downloaded music.
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))

        ctx.voice_client.play(source, after = lambda e: print(f"Player error: {e}") if e else None)

        await ctx.send("Now playing: {}".format(query))

    @commands.command()
    async def stream(self, ctx, *, url):
        # This supports taking string arguement as well
        # e.g `s.play Marshmello - happier` will work too
        # I guess it fetches the first results from the API
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(
                player, after = lambda e: print(f"Player error: {e}") if e else None
            )
        await ctx.send("Now playing: {}".format(player.title))

    @commands.command()
    async def stop(self, ctx):
        ctx.voice_client.pause()
        await ctx.voice_client.disconnect()

    @play.before_invoke
    @stream.before_invoke
    async def ensure_voice_is_connected(self, ctx):
        if ctx.voice_client is None:

            if ctx.author.voice:
                await ctx.author.voice.channel.connect()

            else:
                await ctx.send("Join a voice channel first dumbass.")
                raise commands.CommandError()

        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

def setup(bot):
    bot.add_cog(Music(bot))