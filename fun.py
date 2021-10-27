from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        resp = await ctx.send("Pinging...")
        diff = resp.created_at - ctx.message.created_at
        return await resp.edit(
            content = f"Pong! latency -> {int(self.bot.latency * 1000)} ms! \nRoundtrip -> {1000*diff.total_seconds()}ms!"
        )

def setup(bot):
    bot.add_cog(Fun(bot))