import discord, json
from discord.ext import commands

class Moderation(commands.Cog):

    def __init__(self, client, config):
        self.client = client
        self.config = config
        
    @commands.Cog.listener()
    async def on_raw_message_delete(self, rawMessage):
        guild = self.client.get_guild(rawMessage.guild_id)
        channel = self.client.get_channel(rawMessage.channel_id)
        # If the message was sent before the bot was logged on, it is unfortunately innaccessible. Ignore also if the author is on the whitelist or if the channel is locked (The lock channel command deletes the message of the sender automatically)
        if not rawMessage.cached_message or channel.name in self.config.reportingChannels or rawMessage.cached_message.author.name in self.config.whitelist or channel.name in self.config.lockedChannels:
            return    
        message = rawMessage.cached_message
        member = guild.get_member(message.author.id)
        # Ignore deleted messages if the member no longer exists, they are a bot, or if this functionality is disabled 
        if member == None or member.bot or self.config.moderationChannelName == "":
            return
        moderationChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.moderationChannelName)
        
        # People with trusted roles will likely have access to the log channel for deleted messages
        # Getting a ping every time might get annoying, so don't ping people with trusted roles.
        user = message.author.mention
        if self.config.checkPerms(message.author, author=True):
            user = message.author.name
            
        if len(message.attachments) == 0: # There are no attachments, it was just text
            await moderationChannel.send(user + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content)
        else: #There was an attachment
            if message.content != "":
                await moderationChannel.send(user + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content + "\n\nAnd had the following attachment(s)")
            else:
                await moderationChannel.send(user + " deleted a message in " + message.channel.mention + ". The message consisted of the following attachement(s)")
            for i in message.attachments:
                # The cached attachment URL becomes invalid after a few minutes. The following ensures valid media is accessible for moderation purposes
                await i.save(i.filename, seek_begin=True, use_cached=False) # Save the media locally from the cached URL before it becomes invalid
                file = discord.File(fp=i.filename,) # Create a discord file object based on this saved media
                await moderationChannel.send(content=None,file=file) # Reupload the media to the log channel
                os.remove(i.filename) # Remove the local download of the media
                
    @commands.Cog.listener()
    async def on_raw_message_edit(self, rawMessage):
        # If the message was sent before the bot was logged on, it is unfortunately innaccessible. Ignore also if the author is on the whitelist
        if not rawMessage.cached_message or rawMessage.cached_message.author.name in self.config.whitelist:
            return
        guild = self.client.get_guild(rawMessage.cached_message.author.guild.id)
        channel = self.client.get_channel(rawMessage.channel_id)
        member = guild.get_member(rawMessage.cached_message.author.id)

        # Ignore deleted messages if the member no longer exists, they are a bot, or if this functionality is disabled 
        if member == None or member.bot or self.config.moderationChannelName == "":
            return

        # Try and grab the data of the message and any attachments
        before = rawMessage.cached_message.content
        try:
            after = rawMessage.data["content"]
        except:
            return
        beforeAttach = rawMessage.cached_message.attachments
        afterAttach = rawMessage.data["attachments"]

        #Pinning a message triggers an edit event. Ignore it
        if before == after and len(beforeAttach) == len(afterAttach):
            return

        # Inform the moderation team
        moderationChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.moderationChannelName)
        if before == "":
            before = "<<No message content>>"
        if after == "":
            after = "<<No message content>>"

        # People with trusted roles will likely have access to the log channel for edited messages
        # Getting a ping every time might get annoying, so don't ping people with trusted roles.
        user = rawMessage.cached_message.author.mention
        if self.config.checkPerms(rawMessage.cached_message.author, author=True):
            user = rawMessage.cached_message.author.name
        await moderationChannel.send(user + " just edited their message in " + channel.mention + ", they changed their original message which said \n\n" + before + "\n\nTo a new message saying \n\n" + after)

        if len(rawMessage.cached_message.attachments) != len(rawMessage.data["attachments"]):
            await moderationChannel.send("They also changed the attachments as follows. Before: ")
            for i in beforeAttach: # See message delete function for details of the following
                await i.save(i.filename, seek_begin=True, use_cached=False)
                file = discord.File(fp=i.filename,)
                await moderationChannel.send(content=None,file=file)
                os.remove(i.filename)
            await moderationChannel.send("After:")
            for i in afterAttach:
                await i.save(i.filename, seek_begin=True, use_cached=False)
                file = discord.File(fp=i.filename,)
                await moderationChannel.send(content=None,file=file)
                os.remove(i.filename)

    @commands.command("lock")
    async def lock(self, msg, *args):
        if not self.config.checkPerms(msg): # Check the user has a role in trustedRoles
            await msg.channel.send(self.config.permsError)
            return

        # If no arguments are given, assume the channel the message was sent in should be locked
        if len(args) == 0:
            channel = msg.channel
        else:
            channel = discord.utils.get(self.client.get_all_channels(), guild__name=msg.guild.name, name=args[0])

        # Find the role that affects send message permissions in this channel
        roleName = channel.name.upper()
        guild = msg.guild
        role = None
        for i in guild.roles:
            if i.name == roleName:
                role = i

        # The role name needs to match the uppercase version of the channel name. This will be the case if channels have been made with the automatic channel creation
        if role == None:
            await channel.send("Channel can not be locked")
            return

        # Lock the channel
        self.config.lockedChannels.append(channel.name)
        await msg.message.delete(delay=None)
        await msg.channel.set_permissions(role, read_messages=True, send_messages=False)
        data = {'channels':self.config.lockedChannels}

        # Set up a way to unlock the channel
        message = await channel.send("Channel locked! React with trusted permissions to unlock!")
        await message.add_reaction("🔓") 

        # Save the list of currently locked channels incase the bot goes offline
        f = open("locked.dat", "w")
        json.dump(data, f)
        f.close()

    # Reaction add event specific to unlocking channels
    # For the reaction add event regarding assigning roles, check RoleMenu cog
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.member.bot: # Ignore reaction remove and add events from itself (when editing the menu)
            return
        
        # Grab necessary data to analyse the event
        channel = self.client.get_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)

        # Check first if the reaction is for a channel that is currently locked
        if channel.name in self.config.lockedChannels:
            roleName = msg.channel.name.upper()
            guild = channel.guild
            
            role = None
            for i in guild.roles:
                if i.name == roleName:
                    role = i

            if role == None:
                return
            if reaction.emoji.name == "🔓" and self.config.checkPerms(reaction.member, author=True):
                await msg.channel.set_permissions(role, read_messages=True, send_messages=None)
                self.config.lockedChannels.remove(msg.channel.name)
                data = {'channels':self.config.lockedChannels}

                await msg.delete(delay=None)

                f = open("locked.dat", "w")
                json.dump(data, f)
                f.close()
            return
