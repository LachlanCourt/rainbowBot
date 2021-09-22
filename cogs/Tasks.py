import discord, json, datetime
from discord.ext import commands
from discord.ext import tasks

from cogs.Moderation import Moderation

class Tasks(commands.Cog):

    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.printer.start()

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

    
    @tasks.loop(seconds=5.0) # Change to minutes
    async def printer(self):
        # Reads file in the same format as crontab
        # Minute Hour Date Month Day
        f = open("tasks.json")
        data = json.load(f)
        f.close()
        tasks = data["tasks"]

        for i in tasks:
            if isNow(i[0]):
                if i[1] == "lock":
                    # Generate message object

                    # Get log channel
                    # Send lock message
                    # Save returned message
                    Moderation.lock(self, message, i[2])
        
        print(tasks)
