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
            if self.isNow(task[0]):
                if task[1] == "lock":
                    # Get log channel
                    logChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.logChannelName)
                    # Send lock message
                    message = await logChannel.send("Locking channel " + task[2] + "...")
                    # Save returned message
                    await Moderation.lock(self, message, task[2])
            if task[1] == "lock" and task[3] == "until" and self.isNow(task[4]):
                
                if task[2] in list(self.config.lockedChannels.values()):
                    messageID = None
                    for i in self.config.lockedChannels:
                        if self.config.lockedChannels[i] == task[2]:
                            messageID = i
                    logChannel = discord.utils.get(self.client.get_all_channels(), guild__name=guild.name, name=self.config.logChannelName)
                    message = await logChannel.fetch_message(int(messageID))
                    # Remove and then re-add the reaction to trigger the normal unlock process
                    await Moderation.unlock(self, message, task[2])
##                    self.config.processReaction = True
##                    await message.clear_reactions()
##                    await message.add_reaction("🔓") 
##                    self.config.processReaction = False
                    
                    
                
        
