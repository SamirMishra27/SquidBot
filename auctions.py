from traceback import print_exception
from disnake import CommandInteraction, Embed, ButtonStyle, Member, MessageInteraction
from disnake.ui import Button, button
from disnake.ext import commands

from customview import CustomView
from utils import Color
from asyncio import sleep, wait as asyncio_wait, ALL_COMPLETED, TimeoutError

class AuctionsView(CustomView):

    def __init__(self, ctx, author, guild, current_bidder = None, *, timeout):
        super().__init__(clear_on_timeout = True, timeout = timeout)
        self.ctx = ctx
        self.author = author

        self.guild = guild
        self.role = guild.get_role(1033371432400474233)
        self.current_bidder = current_bidder

        self.is_cancelled = False
        self.bid_received = False

    def reverse_buttons(self):
        self.children[0], self.children[1] = self.children[1], self.children[0]

    async def interaction_check(self, interaction) -> bool:
        return True

    @button(label = "CANCEL BID", custom_id = "cancel_auction", style = ButtonStyle.red, emoji = "❎")
    async def cancel_bid_button(self, button, interaction):
        if interaction.author.id != self.author.id:
            return await interaction.send("Only the auctioneer can do this.", ephemeral = True)

        self.is_cancelled = True
        await self.on_timeout()

    async def teardown(self):
        await self.message.edit(view = self)

class AuctionBidButton(Button):

    def __init__(self, ctx, author, label, custom_id):
        super().__init__(
            label = label,
            style = ButtonStyle.green,
            custom_id = custom_id,
            emoji = "✋",
            row = None
        )
        self.ctx = ctx
        self.author = author
        self.view: AuctionsView

    async def callback(self, interaction):
        if not self.view.role in interaction.author.roles:
            return await interaction.send("You aren't a team owner", ephemeral=True)
        
        if self.view.bid_received:
            return await interaction.send("Too late.", ephemeral = True)

        if self.view.current_bidder is not None:
            if self.view.current_bidder.id == interaction.author.id:
                return await interaction.send("Can't bet consecutively", ephemeral=True)
        
        self.view.bid_received = True
        # global bid_received
        # bid_received = True
        return await self.view.on_timeout()

class Auction(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def start_bid_timer(self, ctx, timeout, view):

        for i in range(timeout - 10, 0, -1):
            
            if view.bid_received or view.is_cancelled:
                return
            await sleep(1)
        
        # time_left = 5  5
        time_left = 10
        message = await ctx.send(f'I WILL SELL THE PLAYER IN **{time_left}**')

        for i in range(time_left, 0, -1):
            
            if view.bid_received or view.is_cancelled:
                return await message.delete()
            time_left -= 1

            await message.edit(content = f'I WILL SELL THE PLAYER IN **{time_left}**')
            await sleep(0.9)
        
        await message.delete()
        return

    @commands.slash_command(name = "start-auction")
    async def start_auction_slash_command(
        self, 
        ctx: CommandInteraction,
        player_name: str = commands.Param(name = "player-name"),
        base_price: int = commands.Param(name = "base-price", min_value = 1, max_value = 100000000),
        timeout: int = commands.Param(name = "timeout-after", min_value = 10, max_value = 120),
        bid_difference: int = commands.Param(name = "bid-difference", min_value = 10, max_value = 1000000),
        user_id: str = commands.Param(default = "None", name = "user-id")
    ):
        """
        Start an auction bid for a player or item.

        Parameters
        ----------
        player_name: The name of player
        base_price: The initial ask price
        timeout: Maximum timeout before player gets sold
        bid_difference: The maximum bid jump
        user_id: The user id if its a discord Member
        """
        if ctx.author.id not in [278094147901194242, 725729303509205023]:
            return await ctx.send("You can't use this command", ephemeral=True)
        
        embed = Embed(title = "AUCTION ALERT", colour = Color.PURPLE)
        embed.add_field(name = "Player", value = player_name, inline = False)
        embed.add_field(name =  "Base Price", value = base_price, inline = False)
        embed.set_footer(text = "Bid starting in 10 seconds.")

        if user_id != "None":
            user: Member = await ctx.guild.get_or_fetch_member(int(user_id), strict = False)

            if user is not None:
                embed.set_image(url = user.avatar.url if user.avatar is not None else "https://archive.org/download/discordprofilepictures/discordblue.png")

        await ctx.send(embed = embed)
        await sleep(10)

        author = ctx.author
        message = await ctx.original_message()
        ctx = await self.bot.get_context(message)

        bidding_price = base_price
        current_bid_msg = f"Initial Bid **{base_price}**"
        current_bidder = None

        # for i in range(1, 10):
        for i in range(1,200):
            bid_message_id = None

            view = AuctionsView(ctx, author, ctx.guild, current_bidder, timeout = timeout + 4)
            button = AuctionBidButton(ctx, author, f"BID ({bidding_price:,})", custom_id = f"auction_bid-{bidding_price}")

            view.add_item(button)
            view.reverse_buttons()

            def check(inter):
                if inter.channel.id != ctx.channel.id or inter.message.id != bid_message_id:
                    return False

                if inter.author.id == author.id:
                    return True 

                else:
                    return inter.data.custom_id in (f"auction_bid-{bidding_price}") and \
                        (current_bidder is None or inter.author.id != current_bidder.id) and \
                        view.role in inter.author.roles 
                # return True
                # return inter.channel.id == ctx.channel.id and \
                # inter.message.id == bid_message_id and \
                # inter.data.custom_id in (f"auction_bid-{bidding_price}") and \
                # (current_bidder is None or inter.author.id != current_bidder.id) and \
                # view.role in inter.author.roles
            
            view.message = await ctx.send(current_bid_msg, view = view)
            bid_message_id = view.message.id

            done, pending = await asyncio_wait([
                self.bot.wait_for(
                    'message_interaction',
                    timeout = timeout,
                    check = check
                ),
                self.start_bid_timer(ctx, timeout, view)
            ], return_when = ALL_COMPLETED)

            try:
                for item in done:
                    result: MessageInteraction = item.result()

                    if isinstance(result, MessageInteraction):
                        break
                    
                if result.data.custom_id == "cancel_auction":
                    return await ctx.send(f"⚠️ AUCTION INTERRUPTED AND CANCELLED BY {result.author.mention}")

                bidding_price += bid_difference
                current_bidder = result.author
                current_bid_msg = f"Current bid by {current_bidder.mention} **{bidding_price}**"
                continue

            except TimeoutError:
                break

            except Exception as e:
                print_exception(e, e, e.__traceback__)
                pass

        if bidding_price == base_price:
            return await ctx.send(f"**{player_name}** WENT UNSOLD! ❎ #AuctionSells")

        else:
            return await ctx.send(f"**{player_name}** SOLD TO {current_bidder} for {bidding_price} #AuctionSells")

def setup(bot):
    bot.add_cog(Auction(bot))