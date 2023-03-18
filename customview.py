from disnake import Embed, Message, CommandInteraction, MessageInteraction
from disnake.ui import View, Button

class CustomView(View):

    def __init__(self, *, clear_on_timeout, timeout):
        super().__init__(timeout=timeout)
        self.clear_on_timeout: bool = clear_on_timeout

        self.embed: Embed
        self.message: Message

    async def interaction_check(self, interaction) -> bool:
        raise NotImplementedError

    async def resolve_message(self, ctx_or_inter, bot_resp_message: Message = None):

        if isinstance(ctx_or_inter, (CommandInteraction, MessageInteraction)):
            self.message = await ctx_or_inter.original_message()

        else:
            self.message = bot_resp_message

    def get_child_by(self, label = None, id = None) -> Button:

        if label is not None:

            for child in self.children:
                if child.label.lower() == label.lower():
                    return child

        elif id is not None:

            for child in self.children:
                if child.custom_id.lower() == id.lower():
                    return child

        return None

    def disable_all_children(self):
        for child in self.children:
            child.disabled = True

    def enable_all_children(self):
        for child in self.children:
            child.disabled = False

    async def on_timeout(self):
        if self.clear_on_timeout:
            self.clear_items()
        
        await self.teardown()
        self.stop()

    async def teardown(self):
        pass