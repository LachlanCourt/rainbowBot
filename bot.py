import discord, sys, json
from discord.ext import commands

# To hold global configuration and variables
from cogs.GlobalConfig import GlobalConfig

# Import cogs
from cogs.FileHandler import FileHandler
from cogs.Moderation import Moderation
from cogs.RoleMenu import RoleMenu
from cogs.MessageHandler import MessageHandler

# Intents give us access to some additional discord moderation features
intents = discord.Intents.all()
client = commands.Bot(command_prefix="$rain", intents=intents)

# Load config file
whitelist = []
trustedRoles = []
logChannelName = ""
moderationChannelName = ""
reportingChannelsList = []
OAuthToken = None
try:
    f = open('config.json')
    data = json.load(f)
    whitelist = data["whitelisted"]
    trustedRoles = data["trustedRoles"]
    logChannelName = data["logChannel"]
    moderationChannelName = data["moderationChannel"]
    reportingChannelsList = data["reportingChannels"]
    OAuthToken = data["OAuthToken"]
    f.close()
except:
    print("Error loading config file. Please ensure it matches the specifications")
    sys.exit()

# Load role menu file
rolemenuData = {}
try:
    f = open("rolemenu.dat")
    self.rolemenuData = json.load(f)
    f.close()
except:
    pass

# Load locked channel data
lockedChannels = []
try:
    f = open("locked.dat")
    data = json.load(f)
    lockedChannels = data["channels"]
    f.close()
except:
    pass


# Load the global config which will run some file reads and set default variables
config = GlobalConfig(whitelist, trustedRoles, logChannelName, moderationChannelName, reportingChannelsList, OAuthToken, rolemenuData, lockedChannels)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

# Add each of the cogs, passing in the configuration
client.add_cog(FileHandler(client, config))
client.add_cog(Moderation(client, config))
client.add_cog(RoleMenu(client, config))
client.add_cog(MessageHandler(client, config))

# Start bot
try:
    client.run(config.OAuthToken)
    print('Closed')
except:
    print("Error starting bot, check OAuth Token in Config")
