import discord, json, datetime
from discord.ext import commands
from discord.ext import tasks

from cogs.Moderation import Moderation
from cogs.helpers._taskValidator import Validator
from cogs.helpers._storage import Storage


class Tasks(commands.Cog):
    def __init__(self, client, state):
        self.client = client
        self.state = state
        self.sendTick = False
        if len(self.state.registeredTasks) > 0:
            self.log("Starting scheduler")
            self.scheduler.start()

    def log(self, msg):
        self.state.logger.debug(f"Tasks: {msg}")

    @staticmethod
    def isNow(cronStamp):
        now = datetime.datetime.now()
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

    @tasks.loop(minutes=1.0)
    async def scheduler(self):
        # Reads file in the same format as crontab
        # Minute Hour Date Month Day
        for filename in self.state.registeredTasks.keys():
            guildId = self.state.registeredTasks[filename]
            valid, n = Validator.validate(filename)
            if not valid:
                continue
            f = open(filename)
            data = json.load(f)
            f.close()
            tasks = data["tasks"]

            guild = None
            for i in self.client.guilds:
                if i.id == guildId:
                    guild = i
            if guild == None:
                return

            if self.sendTick:
                logChannel = discord.utils.get(
                    self.client.get_all_channels(),
                    guild__name=guild.name,
                    name=self.state.logChannelName,
                )
                await logChannel.send(
                    "Status tick for task loop. Ticks are only sent once per `taskstatus` command"
                )
                self.sendTick = False

            for task in tasks:
                start = task[0]
                command = task[1]
                args = task[2]
                preposition = task[3]
                end = task[4]
                if command == "lock":
                    # Only lock channel if it is not already locked
                    if self.isNow(start) and args not in list(
                        self.state.lockedChannels.values()
                    ):
                        # Get log channel
                        logChannel = discord.utils.get(
                            self.client.get_all_channels(),
                            guild__name=guild.name,
                            name=self.state.logChannelName,
                        )
                        # Send lock message
                        message = await logChannel.send(f"Locking channel {args}...")
                        # Lock channel specified
                        await Moderation.lock(self, message, args, True)
                        self.log(f"Channel {args} locked automatically")
                    if preposition == "until" and self.isNow(end):
                        if args in list(self.state.lockedChannels.values()):
                            messageID = None
                            for i in self.state.lockedChannels:
                                if self.state.lockedChannels[i] == args:
                                    messageID = i
                            logChannel = discord.utils.get(
                                self.client.get_all_channels(),
                                guild__name=guild.name,
                                name=self.state.logChannelName,
                            )
                            message = await logChannel.fetch_message(int(messageID))
                            # Call the unlock function on the channel which will delete the message
                            await Moderation.unlock(
                                self, message, args, calledFromTask=True
                            )
                            self.log(f"Channel {args} unlocked automatically")

    # High level authorisation required
    @commands.command("checktask")
    async def checktask(self, msg, *args):
        self.log("Check task command receieved")
        if not self.state.checkPerms(
            msg.message.author
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.state.permsError)
            return
        if len(args) == 0:
            await msg.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"

        valid, response = Validator.validate(filename)
        await self.state.sendLongMessage(response, msg.channel, splitOnDelimeter=True)

    # High level authorisation required
    @commands.command("taskstatus")
    async def taskstatus(self, msg):
        self.log("Taskstatus command receieved")
        # Not that if the last task has only just been removed, this function will return a false positive for the
        # minute afterwards as the loop doesn't properly stop until the minute is up in order to close gracefully
        if not self.state.checkPerms(
            msg.message.author
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.state.permsError)
            return
        if self.scheduler.is_running():
            n = "\n" + ("\n" if len(self.state.registeredTasks) > 0 else "")
            files = n + "\n".join(self.state.registeredTasks.keys()) + n
            await msg.channel.send(
                f"Task loop is running, watching the following files:{files}Status tick will be sent to {self.state.logChannelName} within one minute"
            )
            self.sendTick = True
        else:
            await msg.channel.send(
                "Task loop is stopped. Add a task with `addtask` to start the loop"
            )

    # High level authorisation required
    @commands.command("addtask")
    async def addtask(self, msg, *args):
        self.log("Addtask command receieved")
        if not self.state.checkPerms(
            msg.message.author
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.state.permsError)
            return
        if len(args) == 0:
            await msg.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"

        if "/" in filename or "\\" in filename:
            await msg.channel.send("Cannot use relative filepaths or subdirectories")
            return

        valid, response = Validator.validate(filename)
        if valid and filename not in self.state.registeredTasks:
            self.state.registeredTasks[filename] = msg.guild.id
            Storage.save(self)
            await msg.channel.send(f"Task file {filename} registered successfully")
            if not self.scheduler.is_running():
                self.scheduler.start()
        elif valid:
            await msg.channel.send(
                "That task file has already been registered! Use the `taskstatus` for a list of currently registered tasks"
            )
        else:
            await msg.channel.send(f"Invalid filename {args[0]}")

    # High level authorisation required
    @commands.command("remtask")
    async def remtask(self, msg, *args):
        self.log("Remtask command receieved")
        if not self.state.checkPerms(
            msg.message.author
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.state.permsError)
            return
        if len(args) == 0:
            await msg.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"

        if filename in self.state.registeredTasks:
            del self.state.registeredTasks[filename]
            Storage.save(self)
            await msg.channel.send(f"Task file {filename} unregistered successfully")
            if len(self.state.registeredTasks) == 0:
                self.scheduler.stop()
        else:
            await msg.channel.send(f"Task file {filename} is not currently registered")
