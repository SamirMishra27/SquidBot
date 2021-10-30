from discord.ext import commands

# Eval command imports
import discord
import asyncio
import datetime
from re import sub
from os import getcwd
from io import StringIO
from textwrap import indent
from traceback import format_exception
from contextlib import redirect_stdout

class Owner(commands.Cog, command_attrs = dict(hidden = True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ["e", "eval"])
    @commands.is_owner()
    async def _evaluate(self, ctx, *, arg):
        def clean_code(content):
            if content.startswith("```") and content.endswith("```"):
                return "\n".join(content.split("\n")[1:])[:-3]
            else:
                return content

        code = clean_code(arg)
        local_variables = {
            'ctx': ctx,
            'discord': discord, 
            'bot': self.bot,
            'author': ctx.author,
            'asyncio': asyncio,
            'datetime': datetime,
            'guild': ctx.guild
        }
        stdout = StringIO()
        try:
            with redirect_stdout(stdout):
                exec(
                    f"async def function():\n{indent(code, '    ')}",
                    local_variables
                )
                obj = await local_variables["function"]()
                result = (f"--*Output*```python\n{stdout.getvalue()}\n---```\n" +\
                         f"--*RETURN VALUE* ```python\n{obj}```")
                result = sub(r'([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})', 'Redacted', result)

        except Exception as e:

            result = "```python\n"
            result += "".join(format_exception(e, e, e.__traceback__)) + "```"
            result = result.replace('c' + str(getcwd())[1:] + '''\owner.py''', "YOU MUST NOT SEE THIS PATH KEKW")

        return await ctx.send(result)

def setup(bot):
    bot.add_cog(Owner(bot))