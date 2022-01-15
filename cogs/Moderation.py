import discord, json, os
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
        if (
            not rawMessage.cached_message
            or channel.name in self.config.reportingChannels
            or rawMessage.cached_message.author.name in self.config.whitelist
            or channel.name in list(self.config.lockedChannels.values())
            or rawMessage.cached_message.content.startswith("$rain")
        ):
            return
        message = rawMessage.cached_message
        member = guild.get_member(message.author.id)
        # Ignore deleted messages if the member no longer exists, they are a bot, or if this functionality is disabled
        if member == None or member.bot or self.config.moderationChannelName == "":
            return
        moderationChannel = discord.utils.get(
            self.client.get_all_channels(),
            guild__name=guild.name,
            name=self.config.moderationChannelName,
        )

        # People with trusted roles will likely have access to the log channel for deleted messages
        # Getting a ping every time might get annoying, so don't ping people with trusted roles.
        user = message.author.mention
        if self.config.checkPerms(message.author, level=2):
            user = message.author.name

        if len(message.attachments) == 0:  # There are no attachments, it was just text
            await moderationChannel.send(
                f"{user} deleted a message in {message.channel.mention}. The message was: \n\n{message.content}"
            )
        else:  # There was an attachment
            if message.content != "":
                await moderationChannel.send(
                    f"{user} deleted a message in {message.channel.mention}. The message was: \n\n{message.content}\n\nAnd had the following attachment(s)"
                )
            else:
                await moderationChannel.send(
                    f"{user} deleted a message in {message.channel.mention}. The message consisted of the following attachement(s)"
                )
            for i in message.attachments:
                # The cached attachment URL becomes invalid after a few minutes. The following ensures valid media is accessible for moderation purposes
                await i.save(
                    i.filename, seek_begin=True, use_cached=False
                )  # Save the media locally from the cached URL before it becomes invalid
                file = discord.File(
                    fp=i.filename,
                )  # Create a discord file object based on this saved media
                await moderationChannel.send(
                    content=None, file=file
                )  # Reupload the media to the log channel
                os.remove(i.filename)  # Remove the local download of the media

    @commands.Cog.listener()
    async def on_raw_message_edit(self, rawMessage):
        # If the message was sent before the bot was logged on, it is unfortunately innaccessible. Ignore also if the author is on the whitelist
        if (
            not rawMessage.cached_message
            or rawMessage.cached_message.author.name in self.config.whitelist
        ):
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

        # Pinning a message triggers an edit event. Ignore it
        if before == after and len(beforeAttach) == len(afterAttach):
            return

        # Inform the moderation team
        moderationChannel = discord.utils.get(
            self.client.get_all_channels(),
            guild__name=guild.name,
            name=self.config.moderationChannelName,
        )
        if before == "":
            before = "<<No message content>>"
        if after == "":
            after = "<<No message content>>"

        # People with trusted roles will likely have access to the log channel for edited messages
        # Getting a ping every time might get annoying, so don't ping people with trusted roles.
        user = rawMessage.cached_message.author.mention
        if self.config.checkPerms(rawMessage.cached_message.author, level=2):
            user = rawMessage.cached_message.author.name
        await moderationChannel.send(
            f"{user} just edited their message in {channel.mention}, they changed their original message which said\n\n{before}\n\nTo a new message saying\n\n{after}"
        )

        if len(rawMessage.cached_message.attachments) != len(
            rawMessage.data["attachments"]
        ):
            await moderationChannel.send(
                "They also changed the attachments as follows. Before: "
            )
            for (
                i
            ) in (
                beforeAttach
            ):  # See message delete function for details of the following
                await i.save(i.filename, seek_begin=True, use_cached=False)
                file = discord.File(
                    fp=i.filename,
                )
                await moderationChannel.send(content=None, file=file)
                os.remove(i.filename)
            await moderationChannel.send("After:")
            for i in afterAttach:
                await i.save(i.filename, seek_begin=True, use_cached=False)
                file = discord.File(
                    fp=i.filename,
                )
                await moderationChannel.send(content=None, file=file)
                os.remove(i.filename)

    # Low level authorisation required
    @commands.command("lock")
    async def lock(self, msg, *args):
        if not self.config.checkPerms(
            msg.author, level=2
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.config.permsError)
            return

        # If no arguments are given, assume the channel the message was sent in should be locked
        if len(args) == 0:
            channel = msg.channel
        else:
            # Try as given, lowercase and uppercase
            options = [args[0], args[0].lower(), args[0].upper()]
            channel = None
            for name in options:
                channel = discord.utils.get(
                    self.client.get_all_channels(),
                    guild__name=msg.guild.name,
                    name=name,
                )
                if channel != None:
                    break
            if channel == None:
                await msg.channel.send(
                    f'Channel "{args[0]}" not found. Please check your spelling'
                )
                return

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

        # Set up a way to unlock the channel
        dynamicContent = (
            ("") if (channel.name == msg.channel.name) else (f" {channel.mention}")
        )  # This doesn't work inside an f string so it has been pulled out
        message = await msg.channel.send(
            f"Channel{dynamicContent} locked! React with trusted permissions to unlock"
        )
        await message.add_reaction("🔓")

        # Add the locked channel to the list so that it can be unlocked again
        self.config.lockedChannels[str(message.id)] = channel.name
        # Delete the command message. If this comes as a command then the first line will run, if it is called from Tasks cog then the second line will run
        if len(args) > 1 and args[1]:
            await msg.delete(delay=None)
        else:
            await msg.message.delete(delay=None)

        # Lock channel
        await channel.set_permissions(role, read_messages=True, send_messages=False)
        data = {"channels": self.config.lockedChannels}

        # Save the list of currently locked channels incase the bot goes offline
        f = open("locked.dat", "w")
        json.dump(data, f)
        f.close()

    # Reaction add event specific to unlocking channels
    # For the reaction add event regarding assigning roles, check RoleMenu cog
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.member.bot:  # Ignore reaction remove and add events from itself
            return

        # Grab necessary data to analyse the event
        messageChannel = self.client.get_channel(reaction.channel_id)
        message = await messageChannel.fetch_message(reaction.message_id)

        # Check first if the reaction is for a channel that is currently locked
        if str(message.id) in self.config.lockedChannels:
            # Get the channel that was locked

            if reaction.emoji.name == "🔓" and self.config.checkPerms(
                reaction.member, level=2
            ):
                await self.unlock(message, self.config.lockedChannels[str(message.id)])

    async def unlock(self, message, channelName):
        channel = discord.utils.get(
            self.client.get_all_channels(),
            guild__name=message.guild.name,
            name=channelName,
        )
        guild = channel.guild

        roleName = self.config.lockedChannels[str(message.id)].upper()
        role = self.config.getRole(roleName, guild)
        if role == None:
            return

        await channel.set_permissions(role, read_messages=True, send_messages=None)
        del self.config.lockedChannels[str(message.id)]
        data = {"channels": self.config.lockedChannels}

        await message.delete(delay=None)

        f = open("locked.dat", "w")
        json.dump(data, f)
        f.close()
        return
