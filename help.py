from disnake.ext import commands
from disnake import Embed, Colour
from datetime import datetime

class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__(verify_checks = False)

    async def send_bot_help(self, mapping):

        bot = self.context.bot
        embed = Embed(
            title = "Wassup Nerd",
            timestamp = datetime.now(),
            colour = Colour.dark_magenta()
        )

        for cog, commands in mapping.items():
            cog_name = getattr(cog, '__cog_name__', 'Others')
            if cog_name in ('Owner', 'Jishaku', 'Events', 'Others', 'Auction'):
                continue

            command_list = ""
            for number, command in enumerate(commands, start = 1):
                if command.hidden == True:
                    continue
                command_list += "{} {}\n".format("🔸" if number % 2 == 0 else "🔹", command.name)
                
            embed.add_field(
                name = "**{}** commands\n".format(cog_name),
                value = "\n{}".format(command_list),
                inline = False
            )

        # slash_list = ""
        # for command in commands:
        #     slash_list += "**/**{}\n".format(command.name)
        # embed.add_field(name = "Slash Commands", value = slash_list)  

        embed.description = (
            "Hi, I am Squid. {}\n".format(bot._emojis["sw"]) + \
            "Yell at <@278094147901194242> for things related to this bot.\n" 
        )
        avatar = self.context.author.display_avatar

        embed.set_author(name = bot.user.name, url = "https://youtu.be/fWa3Mi9vSzo", icon_url = avatar)
        embed.set_footer(text = "{}help <command name> for more help.".format(bot.prefix))

        await self.get_destination().send(embed = embed)

class Help(commands.Cog):

    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self
        self.bot = bot
        self.cog_brief = "Help command"
        self.cog_description = "Shows this command"

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

def setup(bot):
    bot.add_cog(Help(bot))