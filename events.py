from discord.ext import commands
from asyncio import TimeoutError

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_typing")
    async def on_typing(self, channel, user, time):
        target = 9696969696969
        if user.id == target:
            try:
                await self.bot.wait_for(
                    'message', timeout = 30, 
                    check = lambda x: x.author.id == target 
                    and x.channel.id == channel.id
                )
            except TimeoutError:
                await channel.send("{} I see you're lurking. :thumbsdown:".format(user.mention))

def setup(bot):
    bot.add_cog(Events(bot))