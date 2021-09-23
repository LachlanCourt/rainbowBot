import discord, json, datetime
from discord.ext import commands
from discord.ext import tasks

from cogs.Moderation import Moderation

class Tasks(commands.Cog):

    def __init__(self, client, config):
        self.client = client
        self.config = config
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

##    @commands.command("test")
##    async def test(self, msg):
##        await Moderation.lock(self, msg, "comp1000")

    
    @tasks.loop(minutes=1.0)
    async def scheduler(self):
        # Reads file in the same format as crontab
        # Minute Hour Date Month Day
        f = open("tasks.json")
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
            channelName = task[2]
            preposition = preposition
            end = task[4]
            if command == "lock":
                if self.isNow(start):
                    # Get log channel
                    logChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.logChannelName)
                    # Send lock message
                    message = await logChannel.send("Locking channel " + channelName + "...")
                    # Save returned message
                    await Moderation.lock(self, message, channelName, True)
                if preposition == "until" and self.isNow(end):
                    if channelName in list(self.config.lockedChannels.values()):
                        messageID = None
                        for i in self.config.lockedChannels:
                            if self.config.lockedChannels[i] == channelName:
                                messageID = i
                        logChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.logChannelName)
                        message = await logChannel.fetch_message(int(messageID))
                        # Call the unlock function on the channel which will delete the message
                        await Moderation.unlock(self, message, channelName)

                    
                    
                
        
