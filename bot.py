import discord
from discord.ext import commands

# To hold global configuration and variables
from cogs.GlobalConfig import GlobalConfig

# Import cogs
from cogs.cogs.FileHandler import FileHandler
from cogs.cogs.Moderation import Moderation
from cogs.cogs.RoleMenu import RoleMenu
from cogs.cogs.MessageHandler import MessageHandler

# Intents give us access to some additional discord moderation features
intents = discord.Intents.all()
client = commands.Bot(command_prefix="$rain", intents=intents)

config = GlobalConfig()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

client.add_cog(FileHandler(client, config))
client.add_cog(Moderation(client, config))
client.add_cog(RoleMenu(client, config))
client.add_cog(MessageHandler(client, config))

try:
    client.run(config.OAuthToken)
    print('Closed')
except:
    print("Error starting bot, check OAuth Token in Config")
