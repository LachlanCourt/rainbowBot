import discord, json, datetime, pytz
from discord.ext import commands
from discord.ext import tasks

from cogs.Moderation import Moderation
from cogs.helpers._taskValidator import Validator
from cogs.helpers._storage import Storage


class Tasks(commands.Cog):
    def __init__(self, client, state):
        self.client = client
        self.state = state
        if self.schedulerShouldStart():
            self.log("Starting scheduler")
            self.scheduler.start()

    def log(self, msg):
        self.state.logger.debug(f"Tasks: {msg}")

    @staticmethod
    def isNow(cronStamp, timezone):
        now = datetime.datetime.now(pytz.timezone(timezone))
        cronStamp = cronStamp.split()

        # Minutes
        if cronStamp[0] != "*":
            nowMins = int(now.strftime("%M"))
            if int(cronStamp[0]) != nowMins:
                return False
        # Hour
        if cronStamp[1] != "*":
            nowHours = int(now.strftime("%H"))
            if int(cronStamp[1]) != nowHours:
                return False

        # Date
        if cronStamp[2] != "*":
            nowDate = int(now.strftime("%d"))
            if int(cronStamp[2]) != nowDate:
                return False

        # Month
        if cronStamp[3] != "*":
            nowMonth = int(now.strftime("%m"))
            if int(cronStamp[3]) != nowMonth:
                return False

        # Day
        if cronStamp[4] != "*":
            nowDay = int(now.strftime("%w"))
            if int(cronStamp[4]) != nowDay:
                return False

        return True

    def schedulerShouldStart(self):
        if self.scheduler.is_running():
            return False
        for guildState in self.state.guildStates.values():
            if len(guildState.registeredTasks) > 0:
                return True
        return False

    @tasks.loop(minutes=1.0)
    async def scheduler(self):
        # Reads file in the same format as crontab
        # Minute Hour Date Month Day
        for guildId in self.state.guildStates.keys():
            guildState = self.state.guildStates[guildId]
            for tasks in guildState.registeredTasks.values():
                guild = self.client.get_guild(int(guildId))

                if guildState._tasksSendTick:
                    logChannel = discord.utils.get(
                        self.client.get_all_channels(),
                        guild__name=guild.name,
                        name=guildState.logChannelName,
                    )
                    await logChannel.send(
                        "Status tick for task loop. Ticks are only sent once per `taskstatus` command"
                    )
                    guildState._tasksSendTick = False

                for task in tasks:
                    start = task[0]
                    command = task[1]
                    args = task[2]
                    preposition = task[3]
                    end = task[4]
                    if command == "lock":
                        # Only lock channel if it is not already locked
                        if self.isNow(start, guildState.timezone) and args not in list(
                            guildState.lockedChannels.values()
                        ):
                            self.log(f"Locking channel {args}")
                            # Get log channel
                            logChannel = discord.utils.get(
                                self.client.get_all_channels(),
                                guild__name=guild.name,
                                name=guildState.logChannelName,
                            )
                            # Send lock message
                            message = await logChannel.send(
                                f"Locking channel {args}..."
                            )
                            # Lock channel specified
                            await Moderation.lock(self, message, args, True)
                            self.log(f"Channel {args} locked automatically")
                        if preposition == "until" and self.isNow(
                            end, guildState.timezone
                        ):
                            if args in list(guildState.lockedChannels.values()):
                                messageID = None
                                for i in guildState.lockedChannels:
                                    if guildState.lockedChannels[i] == args:
                                        messageID = i
                                logChannel = discord.utils.get(
                                    self.client.get_all_channels(),
                                    guild__name=guild.name,
                                    name=guildState.logChannelName,
                                )
                                self.log(
                                    f"Unlocking channel {args} with messageID {messageID} and channel {logChannel.name}"
                                )
                                message = await logChannel.fetch_message(int(messageID))
                                # Call the unlock function on the channel which will delete the message
                                await Moderation.unlock(
                                    self, message, args, calledFromTask=True
                                )
                                self.log(f"Channel {args} unlocked automatically")

    # High level authorisation required
    @commands.command("checktask")
    async def checktask(self, ctx, *args):
        self.log("Check task command receieved")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        if len(args) == 0:
            await ctx.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"

        valid, response = Validator.validate(f"tenants/{ctx.guild.id}/{filename}")
        await self.state.sendLongMessage(response, ctx.channel, splitOnDelimeter=True)

    # High level authorisation required
    @commands.command("taskstatus")
    async def taskstatus(self, ctx):
        self.log("Taskstatus command receieved")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        # Not that if the last task has only just been removed, this function will return a false positive for the
        # minute afterwards as the loop doesn't properly stop until the minute is up in order to close gracefully
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        if len(guildState.registeredTasks) > 0:
            n = "\n" + ("\n" if len(guildState.registeredTasks) > 0 else "")
            files = n + "\n".join(guildState.registeredTasks.keys()) + n
            await ctx.channel.send(
                f"Task loop is running, watching tasks configured from the following files:{files}Status tick will be sent to {guildState.logChannelName} within one minute"
            )
            guildState._tasksSendTick = True
        else:
            await ctx.channel.send(
                "Task loop is stopped. Register a task with `regtask` to start the loop"
            )

    # High level authorisation required
    @commands.command("regtask")
    async def regtask(self, ctx, *args):
        self.log("Regtask command receieved")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        if len(args) == 0:
            await ctx.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"

        if "/" in filename or "\\" in filename or filename == "temp":
            await ctx.channel.send("Cannot use relative filepaths or subdirectories")
            return

        valid, response = Validator.validate(f"tenants/{ctx.guild.id}/{filename}")
        if valid and filename not in guildState.registeredTasks:

            f = open(f"tenants/{ctx.guild.id}/{filename}")
            data = json.load(f)
            f.close()

            guildState.registeredTasks[filename] = data["tasks"]
            Storage(self.state).save()
            await ctx.channel.send(f"Task file {filename} registered successfully")
            if self.schedulerShouldStart():
                self.scheduler.start()
        elif valid:
            await ctx.channel.send(
                "That task file has already been registered! Use the `taskstatus` for a list of currently registered tasks"
            )
        else:
            await ctx.channel.send(f"Invalid file {args[0]}")

    # High level authorisation required
    @commands.command("unregtask")
    async def unregtask(self, ctx, *args):
        self.log("Unregtask command receieved")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        if len(args) == 0:
            await ctx.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"

        if filename in guildState.registeredTasks:
            del guildState.registeredTasks[filename]
            Storage(self.state).save()
            await ctx.channel.send(f"Task {filename} unregistered successfully")
            if self.schedulerShouldStart():
                self.scheduler.stop()
        else:
            await ctx.channel.send(f"Task {filename} is not currently registered")
