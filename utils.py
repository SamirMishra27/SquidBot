from disnake.ext import commands
from math import floor
from time import time
from asyncio import sleep

class CustomContext(commands.Context):

    @property
    def react(self):
        return self.message.add_reaction

    async def send(
        self, *args, **kwargs
    ):
        if self.guild is not None:

            last_timestamp = self.bot.last_message_cache.get(self.channel.id, 0)
            curr_time = time()
            if curr_time - last_timestamp > 1:
                
                self.bot.last_message_cache[self.channel.id] = curr_time
                return await super().send(
                    *args, **kwargs
                )
            else:    
                await sleep(curr_time - last_timestamp) # + 0.2
                
                curr_time = time()
                self.bot.last_message_cache[self.channel.id] = curr_time
                return await super().send(
                    *args, **kwargs
                )
        else:
            last_timestamp = self.bot.last_message_cache.get(self.channel.id, 0)
            curr_time = time()
            if curr_time - last_timestamp > 1:
                
                self.bot.last_message_cache[self.channel.id] = curr_time
                return await super().send(
                    *args, **kwargs
                )
            else:
                await sleep(curr_time - last_timestamp) # + 0.2
                
                curr_time = time()
                self.bot.last_message_cache[self.channel.id] = curr_time
                return await super().send(
                    *args, **kwargs
                )

class CustomVoiceError(commands.CommandError):
    pass

def minutes(time: int) -> str:
    second = int(time % 60)
    if second < 10:
        second = '0' + str(second)
    return f"`{floor(time / 60)}:{second}`"

def membership(track, queue):
    for waiting_track in queue:
        if track.identifier == waiting_track.identifier:
            return True
        continue
    else:
        return False

emojis_dict =  { 
    "sw"     : "<:squidward:903739325857013760>",
    "left"   : "<:leftbutton:964309792573235220>",
    "right"  : "<:rightbutton:964309998966571058>",
    "delete" : "<:deletebutton:964310139152773160>",
    "fastfd" : "<:fastforwardbutton:964518539526561802>",
    "rewind" : "<:rewindbutton:964518561966084137>",
    "x"      : "<:emoji_21:964647871355961414>",
    "hcgold" : "<:HCGold:949029106962550915>"
}
# cSpell: ignore fastfd hcgold rewindbutton squidward leftbutton rightbutton deletebutton fastforwardbutton

class _emojis:
    pass

emojis = _emojis()
for key, value in emojis_dict.items():
        setattr(emojis, key, value)

class Color: #cSpell:ignore Mayablue springgreen basicred tealblue
    MAYABLUE = 0x73C2FB
    SPRINGGREEN = 0x00FA9A
    BASICRED = 0xe74c3c
    PURPLE = 0x9b59ca
    GRAY = 0xa9a9a9
    ORANGE = 0xFC6A03
    TEALBLUE = 0x54BAB9
    BLACK = 0x000000