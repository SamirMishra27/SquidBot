from discord.ui import View, Button, button
from discord import ButtonStyle, Member

class ReplyButtonView(View):
    def __init__(self, text, author, target_user, reply_message):
        super().__init__(timeout = None)
        self.text = text
        self.author = author
        self.target_user = target_user
        self.reply_message = reply_message

    async def interaction_check(self, interaction):
        if interaction.user.id == self.target_user.id:
            return True
        await interaction.response.send_message("This reply is not for you! :thumbsdown:", ephemeral = True)
        return False

    @button(style = ButtonStyle.blurple, label = "Click to see! 📥", disabled = False)
    async def show_reply(self, button, interaction):

        content = "{} said this to you.\n> {}\n\n".format(self.author.mention, self.text)
        if self.reply_message != None:
            content += "**They replied to this message:** \n>>> {}".format(self.reply_message.content)
        await interaction.response.send_message(content = content, ephemeral = True)

laptop_json = {
    "name": "laptop",
    "type": 1,
    "description": "Says hello back!",
    "options": [
        {
            "name": "number",
            "description": "a number.",
            "type": 4,
            "required": True
        },
        {
            "name": "text",
            "description": "additional text.",
            "type": 3,
            "required": False
        }
    ]
}