import discord, os, datetime, pytz, random, string
from discord.ext import commands
from cogs.helpers._storage import Storage


class Moderation(commands.Cog):
    def __init__(self, client, state):
        self.client = client
        self.state = state

    def log(self, msg):
        self.state.logger.debug(f"Moderation: {msg}")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, rawMessage):
        self.log("Message delete event")
        guild = self.client.get_guild(rawMessage.guild_id)
        guildState = self.state.guildStates[str(guild.id)]
        self.state.ensureGuildDirectoryExists(guild.id)
        channel = self.client.get_channel(rawMessage.channel_id)
        # If the message was sent before the bot was logged on, it is unfortunately innaccessible. Ignore also if the author or channel is on the allowlist or if the channel is locked (The lock channel command deletes the message of the sender automatically)
        if (
            not rawMessage.cached_message
            or channel.name in guildState.reportingChannels
            or rawMessage.cached_message.author.name in guildState.userAllowlist
            or channel.name in list(guildState.lockedChannels.values())
            or channel.name in guildState.channelAllowlist
            or rawMessage.cached_message.content.startswith("$rain")
        ):
            self.log("Message not eligible for reposting")
            return
        message = rawMessage.cached_message
        member = guild.get_member(message.author.id)
        # Ignore deleted messages if the member no longer exists, they are a bot, or if this functionality is disabled
        if member == None or member.bot or guildState.moderationChannelName == "":
            return
        moderationChannel = discord.utils.get(
            self.client.get_all_channels(),
            guild__name=guild.name,
            name=guildState.moderationChannelName,
        )

        # People with trusted roles will likely have access to the log channel for deleted messages
        # Getting a ping every time might get annoying, so don't ping people with trusted roles.
        user = message.author.mention
        if guildState.checkPerms(message.author, level=2):
            user = message.author.name

        sanitisedMessage = self.state.sanitiseMentions(message.content, guild)

        # Get the time the message was originally posted. The created_at attribute is in utc format so convert to local time by applying the offset
        rawTime = datetime.datetime.fromisoformat(str(message.created_at))
        time = f"<t:{int(datetime.datetime.timestamp(rawTime))}>"

        if len(message.attachments) == 0:  # There are no attachments, it was just text
            await self.state.sendLongMessage(
                f"{user} deleted a message in {message.channel.mention}. The message was: \n\n{sanitisedMessage}\n\nMessage originally sent at {time}",
                moderationChannel,
            )
        else:  # There was an attachment
            if message.content != "":
                await self.state.sendLongMessage(
                    f"{user} deleted a message in {message.channel.mention}.\n\nMessage originally sent at {time}\n\nThe message was: \n\n{sanitisedMessage}\n\nAnd had the following attachment(s)",
                    moderationChannel,
                )
            else:
                await self.state.sendLongMessage(
                    f"{user} deleted a message in {message.channel.mention}.\n\nMessage originally sent at {time}\n\nThe message consisted of the following attachement(s)",
                    moderationChannel,
                )
            for i in message.attachments:
                # The cached attachment URL becomes invalid after a few minutes. The following ensures valid media is accessible for moderation purposes
                await i.save(
                    f"tenants/{guild.id}/{i.filename}",
                    seek_begin=True,
                    use_cached=False,
                )  # Save the media locally from the cached URL before it becomes invalid
                file = discord.File(
                    fp=f"tenants/{guild.id}/{i.filename}",
                )  # Create a discord file object based on this saved media
                await moderationChannel.send(
                    content=None, file=file
                )  # Reupload the media to the log channel
                os.remove(
                    f"tenants/{guild.id}/{i.filename}"
                )  # Remove the local download of the media

    @commands.Cog.listener()
    async def on_raw_message_edit(self, rawMessage):
        self.log("Message edit event")
        channel = self.client.get_channel(rawMessage.channel_id)
        # If the message was sent before the bot was logged on, it is unfortunately innaccessible. Ignore also if the author or channel is on the allowlist
        if not rawMessage.cached_message:
            self.log(f"Message not eligible for reposting")
            return
        guild = self.client.get_guild(rawMessage.cached_message.author.guild.id)
        guildState = self.state.guildStates[str(guild.id)]
        self.state.ensureGuildDirectoryExists(guild.id)
        if (
            rawMessage.cached_message.author.name in guildState.userAllowlist
            or channel.name in guildState.channelAllowlist
        ):
            self.log(f"User or channel in allowlist, message not reposted")
            return
        member = guild.get_member(rawMessage.cached_message.author.id)

        # Ignore deleted messages if the member no longer exists, they are a bot, or if this functionality is disabled
        if member == None or member.bot or guildState.moderationChannelName == "":
            return

        # Try and grab the data of the message and any attachments
        before = self.state.sanitiseMentions(rawMessage.cached_message.content, guild)
        try:
            after = self.state.sanitiseMentions(rawMessage.data["content"], guild)
        except:
            self.log(f"Edit message after content not available. Early exit")
            return
        beforeAttach = rawMessage.cached_message.attachments
        afterAttach = rawMessage.data["attachments"]

        # Pinning a message triggers an edit event. Ignore it
        if before == after and len(beforeAttach) == len(afterAttach):
            self.log(f"Edit message pin event")
            return

        # Inform the moderation team
        moderationChannel = discord.utils.get(
            self.client.get_all_channels(),
            guild__name=guild.name,
            name=guildState.moderationChannelName,
        )
        if before == "":
            before = "<<No message content>>"
        if after == "":
            after = "<<No message content>>"

        # People with trusted roles will likely have access to the log channel for edited messages
        # Getting a ping every time might get annoying, so don't ping people with trusted roles.
        user = rawMessage.cached_message.author.mention
        if guildState.checkPerms(rawMessage.cached_message.author, level=2):
            user = rawMessage.cached_message.author.name

        # Get the time the message was originally posted. The timestamp attribute is in local format so no need to convert from utc
        rawTime = datetime.datetime.fromisoformat(rawMessage.data["timestamp"])
        time = f"<t:{int(datetime.datetime.timestamp(rawTime))}>"

        await self.state.sendLongMessage(
            f"{user} just edited their message in {channel.mention}, they changed their original message which said\n\n{before}\n\nTo a new message saying\n\n{after}\n\nMessage originally sent at {time}",
            moderationChannel,
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
                await i.save(
                    f"tenants/{guild.id}/{i.filename}",
                    seek_begin=True,
                    use_cached=False,
                )
                file = discord.File(
                    fp=f"tenants/{guild.id}/{i.filename}",
                )
                await moderationChannel.send(content=None, file=file)
                os.remove(f"tenants/{guild.id}/{i.filename}")
            await moderationChannel.send("After:")
            for i in afterAttach:
                await i.save(
                    f"tenants/{guild.id}/{i.filename}",
                    seek_begin=True,
                    use_cached=False,
                )
                file = discord.File(
                    fp=f"tenants/{guild.id}/{i.filename}",
                )
                await moderationChannel.send(content=None, file=file)
                os.remove(f"tenants/{guild.id}/{i.filename}")

    # Low level authorisation required
    @commands.command("lock")
    async def lock(self, ctx, *args):
        self.log("Lock command received")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        self.state.ensureGuildDirectoryExists(ctx.guild.id)
        if not guildState.checkPerms(
            ctx.author, level=2
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return

        # If no arguments are given, assume the channel the message was sent in should be locked
        if len(args) == 0:
            channel = ctx.channel
        elif len(args) == 3:
            await self.addCustomTask(ctx, args)
            return
        else:
            # Try as given, lowercase and uppercase
            options = [args[0], args[0].lower(), args[0].upper()]
            channel = None
            for name in options:
                channel = discord.utils.get(
                    self.client.get_all_channels(),
                    guild__name=ctx.guild.name,
                    name=name,
                )
                if channel != None:
                    break
            if channel == None:
                await ctx.channel.send(
                    f'Channel "{args[0]}" not found. Please check your spelling'
                )
                return

        # Find the role that affects send message permissions in this channel
        role = self.state.getRole(channel.name.upper(), ctx.guild)

        # The role name needs to match the uppercase version of the channel name. This will be the case if channels have been made with the automatic channel creation
        if role == None:
            await channel.send("Channel can not be locked")
            return

        # Set up a way to unlock the channel
        dynamicContent = (
            ("") if (channel.name == ctx.channel.name) else (f" {channel.mention}")
        )  # This doesn't work inside an f string so it has been pulled out
        message = await ctx.channel.send(
            f"Channel{dynamicContent} locked! React with trusted permissions to unlock"
        )
        await message.add_reaction("🔓")

        # Add the locked channel to the list so that it can be unlocked again
        guildState.lockedChannels[str(message.id)] = channel.name
        # Delete the command message. If this comes as a command then the first line will run, if it is called from Tasks cog then the second line will run
        if len(args) == 2 and args[1]:
            await ctx.delete(delay=None)
        else:
            await ctx.message.delete(delay=None)

        # Lock channel
        await channel.set_permissions(role, read_messages=True, send_messages=False)

        # Save the list of currently locked channels incase the bot goes offline
        Storage(self.state).save()

    # Reaction add event specific to unlocking channels
    # For the reaction add event regarding assigning roles, check RoleMenu cog
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.member.bot:  # Ignore reaction remove and add events from itself
            return
        # Grab necessary data to analyse the event
        messageChannel = self.client.get_channel(reaction.channel_id)
        message = await messageChannel.fetch_message(reaction.message_id)
        guildState = self.state.guildStates[str(message.guild.id)]

        # Check if the reaction is for a channel that is currently locked
        if str(message.id) in guildState.lockedChannels:
            if reaction.emoji.name == "🔓" and guildState.checkPerms(
                reaction.member, level=2
            ):
                self.log("Reaction add event to unlock channel")
                await self.unlock(message, guildState.lockedChannels[str(message.id)])

    async def unlock(self, message, channelName, calledFromTask=False):
        self.log("Unlock channel")
        guildState = self.state.guildStates[str(message.guild.id)]
        channel = discord.utils.get(
            self.client.get_all_channels(),
            guild__name=message.guild.name,
            name=channelName,
        )
        guild = channel.guild

        roleName = guildState.lockedChannels[str(message.id)].upper()
        role = self.state.getRole(roleName, guild)
        if role == None:
            return

        await channel.set_permissions(role, read_messages=True, send_messages=None)
        del guildState.lockedChannels[str(message.id)]

        if not calledFromTask:
            await message.delete(delay=None)
        else:
            await message.channel.send(f"Channel {channel.mention} unlocked!")

        Storage(self.state).save()
        return

    async def addCustomTask(self, ctx, args):
        guildState = self.state.guildStates[str(ctx.message.guild.id)]

        now = datetime.datetime.now(pytz.timezone(guildState.timezone))

        requestedStart = args[1].split(":")
        startHours = requestedStart[0]
        startMins = requestedStart[1]
        start = datetime.datetime(
            int(now.strftime("%Y")),
            int(now.strftime("%m")),
            int(now.strftime("%d")),
            int(startHours),
            int(startMins),
            tzinfo=now.tzinfo,
        )

        if start < now:
            # Time comes before today, so the date should be increased
            start += datetime.timedelta(hours=24)

        requestedEnd = args[2].split(":")
        endHours = requestedEnd[0]
        endMins = requestedEnd[1]
        end = datetime.datetime(
            int(start.strftime("%Y")),
            int(start.strftime("%m")),
            int(start.strftime("%d")),
            int(endHours),
            int(endMins),
            tzinfo=start.tzinfo,
        )

        if end < start:
            # Time comes before start, so the date should be increased
            end += datetime.timedelta(hours=24)

        taskId = f"{''.join(random.choice(string.ascii_lowercase + string.digits + string.ascii_uppercase) for i in range(20))}.temp"
        taskData = {
            "tasks": [
                [
                    f"{start:%M %H %d %m *}",
                    "lock",
                    args[0],
                    "until",
                    f"{end:%M %H %d %m *}",
                    1,
                ],
            ]
        }

        guildState.addTaskToState(self.state, self.client, taskId, taskData["tasks"])
        await ctx.channel.send("Task registered successfully")
