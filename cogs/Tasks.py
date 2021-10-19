import discord, json, datetime
from discord.ext import commands
from discord.ext import tasks

from cogs.Moderation import Moderation
from cogs.helpers._taskValidator import Validator

class Tasks(commands.Cog):

    def __init__(self, client, config):
        self.client = client
        self.config = config

    @commands.Cog.listener()
    async def on_ready(self):
        # If there are no registered tasks there is no reason for the scheduler to run
        # Start this in here rather than in init function because init function runs before file read
        # So registeredTasks would always be 0
        if len(self.config.registeredTasks) > 0:
            self.scheduler.start()

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
        for filename in self.config.registeredTasks:
            valid, n = Validator.validate(filename)
            if not valid:
                continue
            f = open(filename)
            data = json.load(f)
            f.close()
            tasks = data["tasks"]

            guild = None
            for i in self.client.guilds:
                if i.name == data["serverName"]:
                    guild = i
            if guild == None:
                return

            for task in tasks:
                start = task[0]
                command = task[1]
                args = task[2]
                preposition = task[3]
                end = task[4]
                if command == "lock":
                    # Only lock channel if it is not already locked
                    if self.isNow(start) and args not in list(self.config.lockedChannels.values()):
                        # Get log channel
                        logChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.logargs)
                        # Send lock message
                        message = await logChannel.send("Locking channel " + args + "...")
                        # Lock channel specified
                        await Moderation.lock(self, message, args, True)
                    if preposition == "until" and self.isNow(end):
                        if args in list(self.config.lockedChannels.values()):
                            messageID = None
                            for i in self.config.lockedChannels:
                                if self.config.lockedChannels[i] == args:
                                    messageID = i
                            logChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.logargs)
                            message = await logChannel.fetch_message(int(messageID))
                            # Call the unlock function on the channel which will delete the message
                            await Moderation.unlock(self, message, args)

    @commands.command("checktask")
    async def checktask(self, msg, *args):
        if not self.config.checkPerms(msg): # Check the user has a role in trustedRoles
            await msg.channel.send(self.config.permsError)
            return
        if len(args) == 0:
            await msg.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"

        valid, response = Validator.validate(filename)
        await msg.channel.send(response)

    @commands.command("addtask")
    async def addtask(self, msg, *args):
        if not self.config.checkPerms(msg): # Check the user has a role in trustedRoles
            await msg.channel.send(self.config.permsError)
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
        if valid:
            self.config.registeredTasks.append(filename)
            f = open("tasks.dat", "w")
            json.dump({"registeredTasks":self.config.registeredTasks}, f)
            f.close()
            await msg.channel.send("Task file " + filename + " registered successfully")
            if not self.scheduler.is_running():
                self.scheduler.start()
        else:
            await msg.channel.send("Invalid filename " + args[0])

    @commands.command("remtask")
    async def remtask(self, msg, *args):
        if not self.config.checkPerms(msg): # Check the user has a role in trustedRoles
            await msg.channel.send(self.config.permsError)
            return
        if len(args) == 0:
            await msg.channel.send("No file specified")
            return

        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"            

        if filename in self.config.registeredTasks:
            self.config.registeredTasks.remove(filename)
            f = open(self.config.tasksFilepath, "w")
            json.dump({"registeredTasks":self.config.registeredTasks}, f)
            f.close()
            await msg.channel.send("Task file " + filename + " unregistered successfully")
            if len(self.config.registeredTasks) == 0:
                self.scheduler.stop()
        else:
            await msg.channel.send("Task file " + filename + " is not currently registered")
      
