import discord, json
from discord.ext import commands

from cogs.Moderation import Moderation

class Tasks(commands.Cog):

    def __init__(self, client, config):
        self.client = client
        self.config = config

    @commands.command("test")
    async def test(self, msg):
        await Moderation.lock(self, msg, "comp1000")
