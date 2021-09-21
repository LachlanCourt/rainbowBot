import discord, json, sys, os, subprocess, re
from discord.ext import commands
from pathlib import Path

# Import state handler
from source.Global.GlobalConfig import GlobalConfig

# Import cogs
from source.cogs.FileHandler import FileHandler
from source.cogs.Moderation import Moderation
from source.cogs.RoleMenu import RoleMenu

# Intents give us access to some additional discord moderation features
intents = discord.Intents.all()
client = commands.Bot(command_prefix="$rain", intents=intents)

config = GlobalConfig()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    # Don't handle messages from ourself
    if message.author == client.user:
        return
    # Messages that have been sent as a direct message to the bot will be reposted in the channel specified in logChannel
    if message.channel.type == discord.ChannelType.private:
        if config.logChannelName == "": # Handle gracefully if no channel is specified to send a DM
            await message.channel.send("I am not set up to receive direct messages, please contact your server administrators another way!")
            return
        await message.channel.send("Thankyou for your message, it has been passed on to the administrators")
        guilds = message.author.mutual_guilds
        for guild in guilds:
            logChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=config.logChannelName)
            await logChannel.send(message.author.mention + " sent a direct message, they said\n\n" + message.content)
    # Messages that are sent into a channel specified in reportingChannels will be deleted and reposted in the specified reporting log with the custom message
    if message.channel.type != discord.ChannelType.private and message.channel.name in config.reportingChannels and message.author.name not in config.whitelist:
        await message.delete(delay=None)
        channel = discord.utils.get(client.get_all_channels(), guild__name=message.guild.name, name=config.reportingChannels[message.channel.name][0])
        replyMessage = config.reportingChannels[message.channel.name][1]
        replyMessage = replyMessage.replace("@user", message.author.mention)
        replyMessage = replyMessage.replace("@message", message.content)
        # If there are multiple different role mentions discord replaces each with <@38473847387837> and we want to ignore these
        # The following matches if an @ symbol is not proceeded by a < symbol, and then matches any number of characters up until the first $ symbol
        matchString = r"(?<!\<)@.*?\$"
        while re.search(matchString, replyMessage) != None:
            roleNameIndex = re.search(matchString, replyMessage).span()
            roleName = replyMessage[roleNameIndex[0] + 1:roleNameIndex[1] - 1]
            role = config.getRole(roleName, message.guild)
            if role != None: # Only replace if the role actually exists. If not, keep searching through replyMessage
                replyMessage = replyMessage.replace(f"@{roleName}$", role.mention)               
        await channel.send(replyMessage)
    # Now that the response to any message has been handled, process the official commands
    await client.process_commands(message)


client.add_cog(FileHandler(client, config))
client.add_cog(Moderation(client, config))
client.add_cog(RoleMenu(client, config))

try:
    client.run(config.OAuthToken)
    print('Closed')
except:
    print("Error starting bot, check OAuth token in Config")
