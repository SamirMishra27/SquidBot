from traceback import print_exception
from disnake.ext import commands
from disnake import DiscordException, Message, Embed, AppCmdInter
from utils import Color
from asyncio import sleep as async_sleep

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.sticky: Message = None
        self.sticky_debounce: bool = False

    @commands.Cog.listener('on_message')
    async def on_message(self, message: Message):

        if message.author.bot:
            return
        
        # if bool("chall" in message.content.lower() and len(message.raw_mentions) == 1) or \
        #     bool(message.interaction and message.interaction.name == "challenge"):
            
        #     return await message.channel.send(embed = Embed(
        #         title = "HOLD UP",
        #         colour = Color.BASICRED,
        #         description = (
        #             "**Is this an HCPL Match?** Remember to follow these instructions below. 👇\n\n"
        #             "1. FORMAT OF THE GAME: 10 OVERS 10 WICKETS\n\n"
        #             "2. REMEMBER TO FOLLOW TOURNAMENT RULES\n\n"
        #             "3. PLAY FAIR AND PLAY WITH RESPECT.\n\n"
        #         )
        #     ))

        if not message.channel.id == 1031296141351985293:
            return

        if self.sticky != None:
            try:
                await self.sticky.delete()
                self.sticky = None
            except Exception:
                pass
        self.sticky = await message.channel.send("Format: \n```\nSAMIR#7795\n```")

    @commands.slash_command(
        name = "cricketfyoodpredict", 
        description = "Predict match results for the ongoing T20 WC in HCL Cricket fyood event.",
        # guild_ids = [794934796761432094]
    )
    @commands.cooldown(1, 120, commands.BucketType.user) #600, 
    async def cricket_fyood_predict_match(
        self, 
        ctx: AppCmdInter, 
        winner_team_name: str = commands.Param(default = None, name = "winning-team", description = "Which country will win the match?"),
        highest_run_scorer: str = commands.Param(default = None, name = "highest-run-scorer", description = "Who will score the most runs? Which batsman? Name one"),
        highest_wicket_taker: str = commands.Param(default = None, name = "highest-wicket-taker", description = "Who will take the most wickets in this match? Name one")
    ):
        if ctx.guild.get_role(1031320581523644476) not in ctx.author.roles:
            ctx.application_command.reset_cooldown(ctx)
            return await ctx.send(
                "You don't have the Cricket fyood role. :x:"
                "Get that role (<@&1031320581523644476>) from <#850366890907533323>",
                ephemeral = True
            )
        
        if not winner_team_name or not highest_run_scorer or not highest_wicket_taker:
            ctx.application_command.reset_cooldown(ctx)
            return await ctx.send(
                "You provided incorrect or did not provide enough inputs for this command.\n"
                "For the match that you are predicting. Enter the __country team__ name that you "
                "think will __win the match__. A __batsman__ who will score the __most runs__ and a __bowler__ "
                "who will take the __most wickets__ according to you.\n"
                "Schedule of upcoming matches ==> https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2022-23-1298134/match-schedule-fixtures-and-results",
                ephemeral = True
            )

        # log_channel = self.bot.get_channel(855025833176334346)
        log_channel = self.bot.get_channel(1031296419069435975)
        embed = Embed(title = "Cricket fyood entry", color = Color.TEALBLUE)

        embed.description = (
            f"Who will win: **`{winner_team_name}`**\n"
            f"Highest run scorer: **`{highest_run_scorer}`**\n"
            f"Highest wicket taker: **`{highest_wicket_taker}`**"
        )
        icon_url = ctx.author.avatar.url if ctx.author.avatar is not None else "https://archive.org/download/discordprofilepictures/discordblue.png"
        embed.set_author(name = f"{ctx.author.name}#{ctx.author.discriminator}", icon_url = icon_url)
        embed.set_footer(text = f"User id: {ctx.author.id}")

        await log_channel.send(embed = embed)
        success = (
            "Successfully counted your entry for the upcoming match ✅\n"
            "Do not send another prediction for this same match again. "
            "It will not be counted. "
            "Come back tomorrow to predict the match results for the next match!"
            "Check the full match schedule and squad here ==> "
            "<https://www.espncricinfo.com/series/icc-men-s-t20-world-cup-2022-23-1298134/match-schedule-fixtures-and-results>"
        )
        await ctx.send(success, ephemeral = True)

    @cricket_fyood_predict_match.error
    async def on_prediction_error(self, ctx, error: DiscordException):

        if isinstance(error, commands.CommandOnCooldown):
            embed = Embed(
                color = Color.BASICRED,
                description = f":x: Command on cooldown, try after {round(error.retry_after, 2)} seconds."
            )
            return await ctx.send(embed = embed, ephemeral = True)

        else: 
            print_exception(error, error, error.__traceback__)
            await ctx.send(error, ephemeral = True)

def setup(bot):
    bot.add_cog(Events(bot))