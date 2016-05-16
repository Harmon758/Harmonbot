
from discord.ext import commands

import keys

def is_owner_check(message):
    return message.author.id == keys.myid

def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))
