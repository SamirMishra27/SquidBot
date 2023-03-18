from disnake import Embed, Colour, VoiceRegion, Member
from disnake.ext import commands

from utils import CustomVoiceError, minutes, membership

from asyncio import sleep as asyncio_sleep
from textwrap import shorten
from math import ceil
# from bs4 import BeautifulSoup

from youtubesearchpython import VideosSearch
import wavelink

from PIL import Image, ImageDraw, ImageFont
from disnake.ui import View, Button, button
from disnake import ButtonStyle
from wavelink.tracks import YouTubeTrack

def to_dict(track: wavelink.YouTubeTrack):
    return {
            "title": f"[{track.title}]({track.uri})",
            "author": track.author,
            "length": minutes(track.length)
        }

class MusicPlayer(View):
    def __init__(self, player: wavelink.Player, bot):
        super().__init__(timeout = 180)
        self.player = player
        self.text_channel_id = player.text_channel.id
        self.voice_channel = player.channel
        self.update_counter = 0
        self.bot = bot

        # self.message when sending the message in command.
        self.stop_player = False

        if player.is_paused() == True:
            self.add_item(ResumeButton())
        else:
            self.add_item(PauseButton())
        self.arrange_button()

    async def interaction_check(self, interaction):
        return interaction.user in self.voice_channel.members

    def arrange_button(self):
        pause_button = self.children[4]
        self.children.remove(pause_button)
        self.children.insert(2, pause_button)

    @button(custom_id = "LAST", style = ButtonStyle.blurple, emoji = "⏮️")
    async def play_last_button(self, button, interaction):
        track: wavelink.YouTubeTrack = self.player.queue.history[-2]
        track_info = to_dict(track)

        self.player.queue.put_at_index(0, track)
        await self.player.stop()
        await interaction.response.send_message("Playing the last played song!")

    @button(label = "-10", custom_id = "REWIND", style = ButtonStyle.blurple, emoji = "⏪")
    async def seek_rewind(self, button, interaction):
        await self.player.seek( (self.player.position-10) * 1000)
        await interaction.response.defer()

    @button(label = "+10", custom_id = "FORWARD", style = ButtonStyle.blurple, emoji = "⏩")
    async def seek_forward(self, button, interaction):
        await self.player.seek( (self.player.position+10) * 1000)
        await interaction.response.defer()

    @button(custom_id = "NEXT", style = ButtonStyle.blurple, emoji = "⏭️")
    async def skip_button(self, button, interaction):
        track = self.player.track 
        await self.player.stop()

        await interaction.response.send_message("Skipped: {}".format(track.title), ephemeral = True)

    async def edit_player(self):
        embed = Embed(title = "Music Player", colour = Colour.fuchsia())

        whats_playing = ""
        if self.player.is_playing():
            track: wavelink.YouTubeTrack = self.player.track
            whats_playing = shorten(track.title, width = 60, placeholder = "...", break_long_words = True) 
        else:
            whats_playing = "No songs playing"

        next_song = ""
        try: 
            track: wavelink.YouTubeTrack = self.player.queue[0]
            next_song = shorten(track.title, width = 50, placeholder = "...", break_long_words = True)
        except: 
            next_song = "No upcoming songs"

        # line = "━━━━━━━━━━●"
        line = list(['━' for i in range(1,11)])
        percentage = (self.player.position/self.player.track.duration) * 10
        line.insert(ceil(percentage), "●")
        line = "".join(line)

        embed.add_field(name = "Now playing", value = whats_playing, inline = False)
        embed.add_field(name = "Upcoming song", value = next_song, inline = False)
        embed.add_field(
            name = f" {minutes(self.player.position)} / {minutes(self.player.track.duration)} ",
            value = line, inline = False
        )
        embed.set_footer(text = f"Requested by: {self.player.track.requested_by.name}")
        embed.set_image(url = self.player.track.thumbnail)

        await self.message.edit(embed = embed)

    async def keep_updating_player(self):
        while True:
            if self.stop_player == True:
                return
            await self.edit_player()
            await asyncio_sleep(1.5)

    async def on_timeout(self) -> None:
        self.stop_player = True
        self.stop()
        for child in self.children:
           child.disabled = True
           await self.message.edit(
                embed = self.message.embeds[0],
                view = self, attachments = []
        )
        return await super().on_timeout()

class PauseButton(Button):
    def __init__(self):
        super().__init__(custom_id = "PAUSE", style = ButtonStyle.gray, emoji = "⏸️")

    async def callback(self, interaction):

        await self.view.player.pause()

        self.view.remove_item(self)
        self.view.add_item(ResumeButton())
        
        print(self.view.children[4])
        self.view.arrange_button()

        await self.view.message.edit(embed = self.view.message.embeds[0], view = self.view, attachments = [])

class ResumeButton(Button):
    def __init__(self):
        super().__init__(custom_id = "RESUME", style = ButtonStyle.green, emoji = "▶️")

    async def callback(self, interaction):
        await self.view.player.resume()

        self.view.remove_item(self)
        self.view.add_item(PauseButton())

        print(self.view.children[4])
        self.view.arrange_button()

        await self.view.message.edit(embed = self.view.message.embeds[0], view = self.view, attachments = [])

class YTSearchView(View):
    def __init__(self, pages: list, user: Member, bot, timeout=180.0):
        super().__init__(timeout = timeout)
        self.user = user
        self.pages = pages
        self.curr_page = 0
        self.bot = bot
        # self.message when sending the message in command.

    @button(custom_id = "BACK", style = ButtonStyle.blurple, emoji = "⬅️") 
    async def page_left(self, button, interaction):
        if self.curr_page -1 < 0:
            pass
        else:
            self.curr_page -= 1
            
        await self.check_disability()

        unpack = self.pages[self.curr_page] # [link, duration]
        content = "Showing page **`{}/{}`**\nDuration: {}\n{}".format(
            self.curr_page, len(self.pages), unpack[1], unpack[0]
        )

        await interaction.response.edit_message(content=content, view=self)

    @button(label = "PLAY NOW", custom_id = "PLAY NOW", style = ButtonStyle.green, emoji = "▶️") 
    async def play_now(self, button, interaction):
        link = self.pages[self.curr_page][0]
        track = await wavelink.YouTubeTrack.search(link, return_first = True)

        context = await self.bot.get_context(self.author_message)
        command = self.bot.get_command("play")

        try:
            await command.prepare(context)
        except Exception as e:
            return await interaction.response.send_message(e, ephemeral = True)
        await command.__call__(context, search = track)
        await interaction.response.defer()
        
    @button(custom_id = "NEXT", style = ButtonStyle.blurple, emoji = "➡️") 
    async def page_right(self, button, interaction):
        if self.curr_page + 1 == len(self.pages):
            pass
        else:
            self.curr_page += 1

        await self.check_disability()

        unpack = self.pages[self.curr_page] # [link, duration]
        content = "Showing page **`{}/{}`**\nDuration: {}\n{}".format(
            self.curr_page, len(self.pages), unpack[1], unpack[0]
        )

        await interaction.response.edit_message(content=content, view=self)

    async def check_disability(self):
        if self.curr_page == 0:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

        if self.curr_page == len(self.pages) - 1:
            self.children[2].disabled = True
        else:    
            self.children[2].disabled = False

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(content = self.message.content, view = self)    
        return await super().on_timeout()

class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        if len(list( wavelink.NodePool().nodes.values() )) > 0:
            return

        await wavelink.NodePool.create_node(
            # host = '127.0.0.1',
            # port = 1900,
            bot = self.bot,
            host = 'lava.link',
            port = 80,
            password = 'youshallnotpass',
            region = VoiceRegion.india
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        print(f'Node: <{node.identifier}> is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track, reason):
        await player.stop()

        if len(player.queue) == 0:
            await player.text_channel.send("The queue has concluded!")

            if hasattr(player, "visualiser") :
                await player.visualiser.on_timeout()

        else:
            track: wavelink.YouTubeTrack = player.queue.get() 
            # get() not only returns the left sided element but also pops it because it is deque internally.
            track_info = to_dict(track)

            await player.play(track)

            embed = Embed(
                title = "Now playing:", color = Colour.fuchsia(),
                description = "{title}\nBy - {author}\nLength - {length}".format(**track_info)
            )
            embed.set_footer(text = "Requested by: {}".format(track.requested_by.name))
            embed.set_thumbnail(url = track.thumbnail)
            await player.text_channel.send(embed = embed)

    @commands.command(aliases = ['vol', 'v'])
    async def volume(self, ctx, volume: int = None):

        if volume == None:
            return await ctx.send("Current volume: {}".format(ctx.voice_client.volume))
        
        if not 101 > volume > 0:
            return await ctx.send("You wanna rip off your ears eh? Input a volume between 1-100 :unamused:")
            
        adjusted_volume = 80 * volume / 100

        await ctx.voice_client.set_volume(50 + adjusted_volume)
        await ctx.send("New volume: **{} %**".format(volume))

        ctx.voice_client.volume_percentage = volume

        # The actual Volume range is between 50 - 130
        # So we adjust the volume accordingly and then add 50 to it.
        # Any volume below 50 and above 130 causes voice quality issues

    @commands.command(aliases = ['p', 'sing'])
    async def play(self, ctx, *, search: wavelink.YouTubeTrack):
        """
        Play a song with the given search query.
        If not connected, connect to our voice channel.
        """
        voice_channel: wavelink.Player = ctx.voice_client

        track: wavelink.YouTubeTrack = search
        track_info = to_dict(track)
        track.requested_by = ctx.author

        if voice_channel.is_playing():
            # If playing a song already then put this to queue

            if voice_channel.track.identifier == track.identifier:
                return await ctx.send("This song is already being played! {}".format(self.bot._emojis["sw"]))

            if membership(track, voice_channel.queue._queue):
                return await ctx.send("Song is already in queue. {}".format(self.bot._emojis["sw"]))

            voice_channel.queue.put(track)

            embed = Embed(
                title = "Added to the queue:", color = Colour.fuchsia(),
                description = (
                    "{title}\nBy - {author}\nLength - {length}\n".format(**track_info) + \
                    "Position: {}".format(voice_channel.queue.find_position(track) + 1)
                ))
            embed.set_footer(text = "Requested by: {}".format(track.requested_by.name))
            embed.set_thumbnail(url = track.thumbnail)
            await ctx.send(embed = embed)

        else:
            # Otherwise go ahead and play it
            await voice_channel.play(track)

            embed = Embed(
                title = "Now playing:", color = Colour.fuchsia(),
                description = "{title}\nBy - {author}\nLength - {length}".format(**track_info)
            )
            embed.set_footer(text = "Requested by: {}".format(track.requested_by.name))
            embed.set_thumbnail(url = track.thumbnail)
            await ctx.send(embed = embed)

    @commands.command(aliases = ['q', 'list'])
    async def queue(self, ctx):
        if ctx.voice_client.queue.count == 0:
            return await ctx.send("There are no songs in queue. :fallen_leaf: :leaves:")
            
        count = ctx.voice_client.queue.count
        embed = Embed(
            title = "Upcoming songs:", 
            color = Colour.blue(), 
            description = ""
        )

        for serialno, track in enumerate(ctx.voice_client.queue, start = 1):
            embed.description += f"{serialno}. " + "**{title}** - {author} (*{length}*)\n\n".format(**to_dict(track))
        
        embed.set_footer(text = "Total songs in the queue - {}".format(count))
        await ctx.send(embed = embed)

    @commands.command()
    async def playnow(self, ctx, *, search: wavelink.YouTubeTrack):
        track: wavelink.YouTubeTrack = search
        track_info = to_dict(track)

        ctx.voice_client.queue.put_at_index(0, track)
        await ctx.voice_client.stop()

    @commands.command(aliases = ['s'])
    async def skip(self, ctx):
        track = ctx.voice_client.track
        await ctx.voice_client.stop()
        await ctx.send("Skipped: {}".format(track.title))

    @commands.command(aliases = ['stop'])
    async def pause(self, ctx):
        if not ctx.voice_client.is_playing():
            return await ctx.send("No songs playing.")
        await ctx.voice_client.pause()
        await ctx.react("⏸️") 

    @commands.command(aliases = ['res', 'cont'])
    async def resume(self, ctx):
        await ctx.voice_client.resume()
        await ctx.react("⏯️") 

    @commands.command(aliases = ['np', 'now playing'])
    async def nowplaying(self, ctx):
        track: wavelink.YouTubeTrack = ctx.voice_client.track
        track_info = to_dict(track)

        embed = Embed(title = "Now playing:", color = Colour.fuchsia())

        embed.description = "{title}\nBy - {author}\n".format(**track_info)
        embed.description += "Currently at - {} / {}".format(minutes(ctx.voice_client.position), minutes(track.length))

        embed.set_footer(text = "Requested by: {}".format(track.requested_by.name))
        embed.set_thumbnail(url = track.thumbnail)
        await ctx.send(embed = embed)

    @commands.command(aliases = ['next', 'ns', 'next song'])
    async def nextsong(self, ctx):
        try:
            track: wavelink.YouTubeTrack = ctx.voice_client.queue[0]
            track_info = to_dict(track)
        except:
            return await ctx.send("There are no songs in queue. :fallen_leaf: :leaves:")

        embed = Embed(title = "Upcoming song:", color = Colour.fuchsia())
        embed.description = "{title}\nBy - {author}\nLength - {length}".format(**track_info)

        embed.set_footer(text = "Requested by: {}".format(track.requested_by.name))
        embed.set_thumbnail(url = track.thumbnail)
        await ctx.send(embed = embed)

    @commands.command(aliases = ['last', 'pl'])
    async def playlast(self, ctx):
        track: wavelink.YouTubeTrack = ctx.voice_client.queue.history[-2]
        track_info = to_dict(track)

        ctx.voice_client.queue.put_at_index(0, track)
        await ctx.voice_client.stop()

        embed = Embed(title = "Playing last song:", color = Colour.fuchsia())
        embed.description = "{title}\nBy - {author}\nLength - {length}".format(**track_info)

        embed.set_footer(text = "Originally requested by: {}".format(track.requested_by.name))
        embed.set_thumbnail(url = track.thumbnail)
        await ctx.send(embed = embed)

    @commands.command(aliases = ['swap'])
    async def queueswap(self, ctx, arg1: int, arg2: int):
        queue: wavelink.WaitQueue = ctx.voice_client.queue
        if arg1 > queue.count or arg2 > queue.count:
            return await ctx.send("Choose numbers within the queue! :x:")

        queue._queue[arg1 - 1], queue._queue[arg2 - 1] = queue._queue[arg2 - 1], queue._queue[arg1 - 1]
        return await ctx.send(
            "The following songs have been swapped! \n" + \
            "*{}*\n".format(queue[arg1 - 1].title) + \
            "🔄 \n" + \
            "*{}*".format(queue[arg2 - 1].title)
        )

    @commands.command(aliases = ['clear'])
    async def queueclear(self, ctx):
        await ctx.send(
            "This action cannot be undone. Are you sure you want to clear the entire queue?" + \
            " {} [yes / no]".format(self.bot._emojis["sw"]))
        try:
            check = lambda x: x.author.id == ctx.author.id and x.channel.id == ctx.channel.id and x.content.lower() in ('yes','no')
            message = await self.bot.wait_for('message', timeout = 30, check = check)
        except Exception:
            return

        if message.content.lower() == "yes":
            ctx.voice_client.queue.clear()
            await ctx.send("Queue has been cleared. ✅")

        else:
            return await ctx.react("✅")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.voice_client.stop()
        await ctx.voice_client.disconnect(force = False)
        await ctx.react("👋")

    @play.before_invoke
    async def ensure_voice_is_connected(self, ctx):
        if ctx.voice_client is None or not ctx.guild.me.voice:

            if ctx.author.voice:
                await ctx.author.voice.channel.connect(cls = wavelink.Player)
                ctx.voice_client.text_channel = ctx.channel
                ctx.voice_client.volume_percentage = 60

            else:
                raise CustomVoiceError("Join a voice channel first dumbass. :microphone2:")

        else:
            if not isinstance(ctx.voice_client, wavelink.Player):
                raise CustomVoiceError("I am currently playing tts voice, make me leave the channel and then use the command again.")

    @commands.command()
    async def player(self, ctx):
        # if ctx.author.id not in self.bot.owner_ids:
        #     raise commands.NotOwner("This command is work in progress!{}".format(self.bot._emojis["sw"]), )
        
        view = MusicPlayer(player = ctx.voice_client, bot = self.bot)  
        ctx.voice_client.visualiser = view
 
        embed = Embed(title = "Music Player")
        message = await ctx.send(view = view, embed = embed)
        view.message = message
        
        return await view.keep_updating_player()

    @commands.command()
    async def ytsearch(self, ctx, *, link_or_query: str):
        link_or_query.strip("<>")

        results = VideosSearch(link_or_query, limit = 10, timeout = 30)
        results = results.result()
        results = results["result"]  # results is a list of dictionaries each containing video info

        pages = []
        for each_video_dict in results:
            link = each_video_dict["link"]
            duration = each_video_dict["accessibility"]["duration"]
            pages.append([link, duration])

        to_send = "Showing page **`1/10`**\nDuration: {}\n{}".format(pages[0][1], pages[0][0])

        view = YTSearchView(pages, ctx.author, self.bot, timeout = 120)
        message = await ctx.send(to_send, view = view)
        
        view.message = message
        view.author_message = ctx.message

def setup(bot):
    bot.add_cog(Music(bot))