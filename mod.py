from traceback import format_exception, print_exception
from disnake.ext import commands
from disnake.ext import tasks
from disnake import Member, Message, Role, TextChannel, PermissionOverwrite

from datetime import datetime, timedelta
from json import dump, load
from time import time
from utils import CustomContext
from typing import Union

with open("tasks.json") as f:
    role_tasks = load(f)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = role_tasks
        self.update_tasks.start()

    def cog_unload(self) -> None:
        self.update_tasks.stop()

    @tasks.loop(minutes = 1)
    async def update_tasks(self):
        to_change = False

        for task in self.tasks:
            if time() - task["last_pinged"] > task["duration"]:
                if task["mentionable"] == True:
                    continue

                guild = self.bot.get_guild(task["guildid"])
                role = guild.get_role(task["roleid"])

                await role.edit(mentionable = True)
                task["mentionable"] = True

                to_change = True
                print(f"role {role.id} set to mentionable")

        if to_change:
            with open("tasks.json", "w") as f:
                dump(self.tasks, f, indent = 4)

    @update_tasks.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()

    # @update_tasks.after_loop
    # async def _after(self):
    #     self.update_tasks.restart()

    @commands.Cog.listener("on_message")
    async def on_message(self, message: Message):

        for task in self.tasks:
            if task["roleid"] in message.raw_role_mentions:

                if task["mentionable"] == False:
                    continue

                task["last_pinged"] = time()

                guild = self.bot.get_guild(task["guildid"])
                role = guild.get_role(task["roleid"])

                await role.edit(mentionable = False)
                task["mentionable"] = False

                print(f"role {role.id} set to unmentionable")
                with open("tasks.json", "w") as f:
                    dump(self.tasks, f, indent = 4)

    @commands.command()
    @commands.has_guild_permissions(moderate_members = True)
    async def mute(self, ctx: CustomContext, member: Union[Member, str] = None, duration: str = None):
        types = {'s': '1', 'm': '60', 'h': '3600', 'd': '86400', 'w': '604800'}

        if isinstance(member, Member) and isinstance(duration, (str, type(None))):
            if not duration:
                duration = "10m"
        
        elif isinstance(member, (str, type(None))) and ctx.message.reference is not None:
            if not duration:
                duration = member or "10m"

            reply_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = reply_message.author

        else:
            raise commands.BadArgument()

        for word in duration:
            if word.lower() in types:
                duration = duration.replace(word, "*" + types[word] + "+")
                # 2h -> 2*3600 -> int()
        duration = duration.rstrip("+")

        try:
            delta = timedelta(seconds = eval(duration))
        except Exception as e:
            return await ctx.send("Invalid time specified!")

        future_date = datetime.now() + delta
        await member.timeout(until = future_date)
        await ctx.send("👌")

    @commands.command()
    @commands.has_guild_permissions(moderate_members = True)
    async def unmute(self, ctx, member: Member = None):

        if member == None and ctx.message.reference is not None:
            reply_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = reply_message.author

        if member == None:
            raise commands.TooManyArguments()

        await member.timeout(until = None)
        await ctx.send("👌")

    @commands.command(aliases = ["sm"])
    @commands.has_guild_permissions(manage_guild = True)
    async def slowmode(self, ctx: CustomContext, slowmode: int):
        await ctx.channel.edit(slowmode_delay = slowmode)
        await ctx.react("👌")

    # @commands.command()
    # @commands.has_guild_permissions(manage_guild = True)
    # async def lockdown(self, ctx: CustomContext, channels: commands.Greedy[TextChannel]):
    #     try:
    #         locked = ""
    #         perm_overwrite = PermissionOverwrite(send_messages = False)

    #         everyone = ctx.guild.default_role
    #         players_role = ctx.guild.get_role(794976763973074964)

    #         for channel in channels:
    #             await channel.edit(overwrites = {everyone: perm_overwrite, players_role: perm_overwrite})
    #             locked += channel.mention + ' '
                
    #         await ctx.send(f'Locked down the following channels: {locked} 🚨')
    #     except Exception as e:
    #         await ctx.send(f'{format_exception(e, e, e.__traceback__)}')

    @commands.command()
    @commands.has_guild_permissions(manage_roles = True)
    async def massrole(self, ctx: CustomContext, role: Role, members: commands.Greedy[Member]):
        if ctx.author.id not in (830132607097896970, 278094147901194242):
            return
        
        success_list = ""
        failed_list = ""
        already_list = ""

        for member in members:
            if role in member.roles:
                already_list += f"*{member.name}* ({member.id})\n"
                continue
            try:
                await member.add_roles(role)
                success_list += f"*{member.name}* ({member.id})\n"
            except Exception:
                failed_list += f"*{member.name}* ({member.id})\n"

        to_send = "Process complete\n\n"
        if success_list:
            to_send += f"Successfully added roles to these users: \n```py\n{success_list}```"
        if failed_list:
            to_send += f"\nFailed to add roles to these users: \n```py\n{failed_list}```"
        if already_list:
            to_send += f"\nThese users already have the specified role: \n```py\n{already_list}```"
        await ctx.send(to_send)
    
    @commands.command()
    @commands.has_guild_permissions(manage_channels = True)
    async def syncpermissions(self, ctx: CustomContext):
        await ctx.channel.edit(sync_permissions=True)
        await ctx.react("✅")

def setup(bot):
    bot.add_cog(Moderation(bot))