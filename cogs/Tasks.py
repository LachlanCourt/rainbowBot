import discord, json
from discord.ext import commands
from discord.ext import tasks

from cogs.Moderation import Moderation

class Tasks(commands.Cog):

    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.printer.start()

##    @commands.command("test")
##    async def test(self, msg):
##        await Moderation.lock(self, msg, "comp1000")

    @tasks.loop(seconds=5.0)
    async def printer(self):
        print("tick")
