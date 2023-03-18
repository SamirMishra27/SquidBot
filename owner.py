from disnake.ext import commands
from utils import Color

# Eval command imports
import disnake
import asyncio
import datetime

from ast import fix_missing_locations, parse, Expr, Return
from re import sub
from os import getcwd, getpid
from io import StringIO, BytesIO
from textwrap import indent
from traceback import format_exception, print_exc
from contextlib import redirect_stdout
from psutil import Process

proc = Process(getpid())
proc.cpu_percent(interval=None)

class Owner(commands.Cog, command_attrs = dict(hidden = True)):
    def __init__(self, bot):
        self.bot = bot

    def return_cog_name(self, cog):
        if not cog.isdecimal():
            for ext in self.bot.bot_exts:
                if cog in ext:
                    cog_name = ext
                    break
        else:
            cog_name = self.bot.bot_exts[int(cog)]
        return cog_name

    @commands.command(aliases = ['r', 'reload'])
    @commands.is_owner()
    async def _reload(self, ctx, cog = None):
        try:
            cog_name = self.return_cog_name(cog)
        except:
            return await ctx.react("❌")

        try:
            self.bot.reload_extension(cog_name)
            return await ctx.message.add_reaction('✅')
        except Exception as e:
            print_exc()
            return await ctx.message.add_reaction('❌')

    @commands.command(aliases = ["e", "eval", "ev"])
    @commands.is_owner()
    async def _evaluate(self, ctx, *, arg):
        print_return_value = False

        def clean_code(content):
            if content.startswith("```") and content.endswith("```"):
                return "\n".join(content.split("\n")[1:])[:-3]
            else:
                return content

        code = f"async def function():\n{indent(clean_code(arg), '    ')}"
        parsed = parse(code)

        if isinstance(parsed.body[-1].body[-1], Expr):
            # Last line is an expression so we will make it print to the chat
            parsed.body[-1].body[-1] = Return(parsed.body[-1].body[-1].value)
            fix_missing_locations(parsed.body[-1].body[-1])
            print_return_value = True

        local_variables = {
            'disnake': disnake, 
            'asyncio': asyncio,
            'datetime': datetime,
            'bot': self.bot,
            'ctx': ctx,
            'author': ctx.author,
            'guild': ctx.guild,
            'voice': ctx.voice_client
        }
        stdout = StringIO()
        try:
            with redirect_stdout(stdout):
                exec(compile(parsed, "<ast>", "exec"), local_variables)
                obj = await local_variables["function"]()

                output = f'{ stdout.getvalue() }'
                if print_return_value and not output:
                    output = f'{ obj }'
                    obj = None

                result = ""
                if len(output) < 1980:
                    result = (
                        f"--*Output*```python\n{output}\n\n---```\n" + \
                        f"--*RETURN VALUE* ```python\n{obj}```"
                    )
                elif len(output) >= 1980:
                    result = output

                TOKEN_REGEX = r'([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})'
                result = sub(TOKEN_REGEX, 'Redacted', result)

        except Exception as e:
            result = "```python\n"
            result += "".join(format_exception(e, e, e.__traceback__)) + "```"

            result = result.replace(getcwd(), "YOU MUST NOT SEE THIS PATH KEKW")

        if len(result) >= 1980:
            return await ctx.send(file = disnake.File(fp = BytesIO(result.encode("utf-8")), filename = "output.py"))
        return await ctx.send(result)

    @commands.command(
        name = 'console', 
        hidden = True, 
        extras = {'examples': None}
    )
    @commands.is_owner()
    async def send_to_console(self, ctx, *, arg):
        print(arg)

    @commands.command(
        name = 'clean',
        extras = {"examples": None}
    )
    @commands.is_owner()
    async def clean_terminal(self, ctx):
        for i in range(1,21):
            print('\u200b')

    @commands.command()
    @commands.is_owner()
    async def stats(self, ctx):

        diff = datetime.datetime.now() - self.bot.launched_at
        ram = round(proc.memory_info().rss/1e6, 2)
        ram_percent = round(proc.memory_percent(), 2)

        cpu_usage = round(proc.cpu_percent(interval=None), 2)
        uptime = round(diff.seconds/60)

        embed = disnake.Embed(title = "Statistics:", colour = Color.GRAY)
        embed.add_field(
            name = "Server system stats:",
            value = '\n'.join(["**RAM**: {}MB  ({})%".format(ram, ram_percent),
            "**CPU**: {}%".format(cpu_usage),
            "**Uptime**: {} days {} hours {} mins.".format(int(diff.days), int(uptime/60), int(uptime%60))])
        )
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed = embed) 

def setup(bot):
    bot.add_cog(Owner(bot))