from traceback import format_exception, print_exception
from disnake.ext import commands
from disnake.ext import tasks
from disnake import Member, Message, Role, TextChannel, PermissionOverwrite

from datetime import datetime, timedelta
from json import dump, load
from time import time
from utils import CustomContext, emojis
from typing import Union

REPORT_EXPIRY_TIME = 50 * 60
with open("tasks.json") as f:
    role_tasks = load(f)

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tasks = role_tasks
        self.update_tasks.start()
        
        with open("reports.json") as f:
            self.reports = load(f)

    def cog_unload(self) -> None:
        self.update_tasks.stop()

        with open("tasks.json", "w") as f:
            dump(self.tasks, f, indent = 4)
        with open("reports.json", "w") as f:
            dump(self.reports, f, indent = 4)

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
    async def _before_tasks(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes = 10)
    async def update_reports(self):
        with open("reports.json") as f:
            dump(self.reports, f, indent = 4)

    @update_reports.before_loop
    async def _before_reports(self):
        await self.bot.wait_until_ready()

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

        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("Not enough permissions 🗿")

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

    @commands.command(aliases = ["mm"])
    @commands.has_guild_permissions(moderate_members = True)
    async def massmute(self, ctx: CustomContext, members: commands.Greedy[Member], duration: str = None):
        types = {'s': '1', 'm': '60', 'h': '3600', 'd': '86400', 'w': '604800'}
        success_members = []
        failed_members = []

        if not duration:
            duration = "10m"

        for word in duration:
            if word.lower() in types:
                duration = duration.replace(word, "*" + types[word] + "+")
                # 2h -> 2*3600 -> int()
        duration = duration.rstrip("+")
        future_date = datetime.now() + timedelta(seconds = eval(duration))

        for member in members:
            if member.top_role >= ctx.guild.me.top_role:
                failed_members.append(member.name)
                continue

            await member.timeout(until = future_date)
            success_members.append(member.name)

        message = ""
        if success_members:
            message += "👌 Muted " + ", ".join([name for name in success_members])

        if failed_members:
            message += "\n👎 Failed to mute " + ", ".join([name for name in failed_members])
        await ctx.send(message)

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

    @commands.command(aliases = ["lk", "lockdown"])
    @commands.has_guild_permissions(manage_guild = True)
    async def lock(self, ctx: CustomContext, channels: commands.Greedy[TextChannel]):
        locked_channels = ""
        failed_to_lock = ""
        message = None

        if not channels:
            channels.append(ctx.channel)

        if len(channels) > 1:
            message = await ctx.send(f"Locking channels {emojis.fro}")

        for channel in channels:
            channel_overwrites = channel.overwrites

            everyone_perm_overwrite = channel_overwrites.get(
                ctx.guild.default_role,
                PermissionOverwrite()
            )
            bot_perm_overwrite = channel_overwrites.get(
                ctx.guild.me, PermissionOverwrite()
            )
            bot_perm_overwrite.send_messages = True
            everyone_perm_overwrite.send_messages = False

            channel_overwrites.update({
                ctx.guild.me: bot_perm_overwrite,
                ctx.guild.default_role: everyone_perm_overwrite
            })
            try:
                await channel.edit(overwrites = channel_overwrites)
                locked_channels += channel.mention + ' '
            except Exception as e:
                print_exception(e,e,e.__traceback__)
                failed_to_lock += channel.mention + ' '

        if message:
            if locked_channels:
                response = f"Locked the following channels ➡️ {locked_channels} ✅\n"
            if failed_to_lock:
                response += f"Failed to lock the following channels ➡️ {failed_to_lock} ❌"
            await message.edit(response)

        elif not message and failed_to_lock:
            await ctx.send(f"Failed to lock {failed_to_lock} ❌")

        else:
            await ctx.react("✅")

    @commands.command(aliases = ["ulk"])
    @commands.has_guild_permissions(manage_guild = True)
    async def unlock(self, ctx: CustomContext, channels: commands.Greedy[TextChannel]):
        unlocked_channels = ""
        failed_to_unlock = ""
        message = None

        if not channels:
            channels.append(ctx.channel)

        if len(channels) > 1:
            message = await ctx.send(f"Unlocking channels {emojis.fro}")

        for channel in channels:
            channel_overwrites = channel.overwrites
            
            everyone_perm_overwrite = channel.overwrites.get(
                ctx.guild.default_role,
                PermissionOverwrite()
            )
            bot_perm_overwrite = channel_overwrites.get(
                ctx.guild.me, PermissionOverwrite()
            )
            bot_perm_overwrite.send_messages = True
            everyone_perm_overwrite.send_messages = True

            channel_overwrites.update({
                ctx.guild.me: bot_perm_overwrite,
                ctx.guild.default_role: everyone_perm_overwrite
            })
            try:
                await channel.edit(overwrites = channel_overwrites)
                unlocked_channels += channel.mention + ' '
            except Exception as e:
                print_exception(e,e,e.__traceback__)
                failed_to_unlock += channel.mention + ' '

        if message:
            if unlocked_channels:
                response = f"Unlocked the following channels ➡️ {unlocked_channels} ✅\n"
            if failed_to_unlock:
                response += f"Failed to unlock the following channels ➡️ {failed_to_unlock} ❌"
            await message.edit(response)

        elif not message and failed_to_unlock:
            await ctx.send(f"Failed to unlock {failed_to_unlock} ❌")

        else:
            await ctx.react("✅")

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
    
    @commands.command(aliases = ["sync"])
    @commands.has_guild_permissions(manage_channels = True)
    async def syncpermissions(self, ctx: CustomContext):
        await ctx.channel.edit(sync_permissions=True)
        await ctx.react("✅")

    def update_member_reports(self, member_reports):

        curr_time = time()
        for report in member_reports:
            if curr_time - report["timestamp"] > REPORT_EXPIRY_TIME:
                member_reports.remove(report)

        return member_reports

    @commands.command()
    @commands.guild_only()
    async def report(self, ctx: CustomContext, member: Member = None):
        REPORT_MUTE_DURATION = 30 * 60
        MAX_REPORTS_FOR_MUTE = 5

        if not member and not ctx.message.reference:
            return await ctx.send("Whom are you reporting? 🗿")
        
        if ctx.message.reference and not member:
            reply_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = reply_message.author

        if member.current_timeout:
            return await ctx.send("Can't report a muted member")

        reports = self.reports[str(ctx.guild.id)]
        member_reports = reports.get(str(member.id), [])

        member_reports = self.update_member_reports(member_reports)
        for report in member_reports:
            if report["user_id"] == ctx.author.id:
                return await ctx.send("You can't report twice")
            
        member_reports.append({
            "user_id": ctx.author.id,
            "timestamp": time()
        })
        await ctx.react("✅")
        if len(member_reports) >= MAX_REPORTS_FOR_MUTE:

            try: await member.timeout(duration = REPORT_MUTE_DURATION)
            except Exception as e: pass

            await ctx.send(f"**{member.name}** was muted after {MAX_REPORTS_FOR_MUTE} reports! 🔇")
            reports.pop(str(member.id))

        else:
            reports[str(member.id)] = member_reports

def setup(bot):
    bot.add_cog(Moderation(bot))