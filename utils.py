from disnake.ext import commands
from math import floor
from time import time
from asyncio import sleep
from json import load

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
                await sleep(curr_time - last_timestamp)
                
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
                await sleep(curr_time - last_timestamp)
                
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

# cSpell:disable
class Color: 
    MAYABLUE = 0x73C2FB
    SPRINGGREEN = 0x00FA9A
    BASICRED = 0xe74c3c
    PURPLE = 0x9b59ca
    GRAY = 0xa9a9a9
    ORANGE = 0xFC6A03
    TEALBLUE = 0x54BAB9
    BLACK = 0x000000

with open("assets/emojis.json") as f:
    emojis_dict = load(f)
    print(emojis_dict["sw"])

# cSpell:enable
class _emojis:
    pass

emojis = _emojis()
for key, value in emojis_dict.items():
    setattr(emojis, key, value)