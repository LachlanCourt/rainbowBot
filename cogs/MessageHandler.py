import discord, json, re
from discord.ext import commands

class MessageHandler(commands.Cog):

    def __init__(self, client, config):
        self.client = client
        self.config = config

    @commands.Cog.listener()
    async def on_message(self, message):
        # Don't handle messages from ourself
        if message.author == self.client.user:
            return
        # Messages that have been sent as a direct message to the bot will be reposted in the channel specified in logChannel
        if message.channel.type == discord.ChannelType.private:
            if self.config.logChannelName == "": # Handle gracefully if no channel is specified to send a DM
                await message.channel.send("I am not set up to receive direct messages, please contact your server administrators another way!")
                return
            await message.channel.send("Thankyou for your message, it has been passed on to the administrators")
            guilds = message.author.mutual_guilds
            for guild in guilds:
                logChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.logChannelName)
                await logChannel.send(message.author.mention + " sent a direct message, they said\n\n" + message.content)
        # Messages that are sent into a channel specified in reportingChannels will be deleted and reposted in the specified reporting log with the custom message
        if message.channel.type != discord.ChannelType.private and message.channel.name in self.config.reportingChannels and message.author.name not in self.config.whitelist:
            await message.delete(delay=None)
            channel = discord.utils.get(self.client.get_all_channels(), guild__name=message.guild.name, name=self.config.reportingChannels[message.channel.name][0])
            replyMessage = self.config.reportingChannels[message.channel.name][1]
            replyMessage = replyMessage.replace("@user", message.author.mention)
            replyMessage = replyMessage.replace("@message", message.content)
            # If there are multiple different role mentions discord replaces each with <@38473847387837> and we want to ignore these
            # The following matches if an @ symbol is not proceeded by a < symbol, and then matches any number of characters up until the first $ symbol
            matchString = r"(?<!\<)@.*?\$"
            while re.search(matchString, replyMessage) != None:
                roleNameIndex = re.search(matchString, replyMessage).span()
                roleName = replyMessage[roleNameIndex[0] + 1:roleNameIndex[1] - 1]
                role = self.config.getRole(roleName, message.guild)
                if role != None: # Only replace if the role actually exists. If not, keep searching through replyMessage
                    replyMessage = replyMessage.replace(f"@{roleName}$", role.mention)               
            await channel.send(replyMessage)
