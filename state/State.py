import os, json, re

from state.GuildState import GuildState
from cogs.helpers._storage import Storage

from github import Github

DISCORD_MAX_MESSAGE_LENGTH = 2000


class State:
    def __init__(self, client, logger):
        self.client = client
        self.logger = logger
        self.guildStates = {}
        # Source files cannot be removed and will not show up with a listfiles command, but they can be overwritten
        # The following is only the files not tracked by git. Source files tracked by git are auto generated in the function below
        self.sourceFiles = [
            ".git",
            "config.json",
            "updatebot.sh",
            "log",
            "data.dat",
            ".profile.d",  # Generated by Heroku deployment
            "runtime.txt",  # Generated by Heroku deployment
            ".heroku",  # Generated by Heroku deployment
        ]
        self.reactions = "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿".split()
        self.permsError = "You don't have permission to use this command"

    async def initialiseGuildStates(self):
        config = {}
        data = {}
        config = None
        if os.environ.get("AMAZON_S3_ACCESS_ID") and os.environ.get(
            "AMAZON_S3_SECRET_ACCESS_KEY"
        ):
            config = Storage().loadConfig()
        if not config:
            try:
                f = open("config.json")
                config = json.load(f)
                f.close()
            except Exception as e:
                print(e)
                raise Exception(e)

        data = Storage(self).load()

        async for (guild) in (
            self.client.fetch_guilds()
        ):  # fetch_guilds limits to 100 for performance reasons. Can override by passing None but will likely need to reconsider if this becomes necessary anyway
            guildState = GuildState(config[str(guild.id)], str(guild.id), self.logger)
            if str(guild.id) in data:
                guildState.initialiseData(data[str(guild.id)])
            else:
                print(
                    f'Error loading data for guild "{guild.name}" with id {guild.id}. Initialising with no persistent data'
                )
            self.guildStates[guild.id] = guildState

    def generateSourceList(self):
        g = Github()
        r = g.get_repo("LachlanCourt/rainbowBot")
        for file in r.get_contents(""):
            self.sourceFiles.append(file.name)

    # Only discord users with a role in the trustedRoles list will be allowed to use bot commands
    # Permission levels start at the strictest level at 0 and go to 2
    def checkPerms(self, author, level=0):
        roleNames = []
        for i in range(len(author.roles)):
            roleNames.append(author.roles[i].name)
        allAllowedRoles = []
        for i in range(level, -1, -1):
            allAllowedRoles += self.trustedRoles[i][:]
        if any(i in roleNames for i in allAllowedRoles):
            return True
        return False

    def getRole(self, roleIdentifier, guild, compareId=False):
        for i in guild.roles:
            if not compareId and i.name == roleIdentifier:
                return i
            if compareId and i.id == roleIdentifier:
                return i
        return None

    def sanitiseMentions(self, message, guild):
        matchString = r"\<@&\d*?\>"
        while re.search(matchString, message) != None:
            roleNameIndex = re.search(matchString, message).span()
            roleId = message[roleNameIndex[0] + 3 : roleNameIndex[1] - 1]
            role = self.getRole(int(roleId), guild, compareId=True)
            if (
                role != None
            ):  # Only replace if the role actually exists. If not, keep searching through replyMessage
                message = message.replace(role.mention, f"@{role.name}")
        return message

    async def sendLongMessage(self, message, channel, splitOnDelimeter=False):
        if len(message) > DISCORD_MAX_MESSAGE_LENGTH * 10:
            self.logger.debug(
                f"State: Message is more than 20000 characters long and has been ratelimited. Message is as follows\n{message}"
            )
            await channel.send("Your request could not be processed")
            raise Exception(
                "Message is more than 20000 characters long and has been ratelimited. Full message available in logs"
            )
        if not splitOnDelimeter:
            chunks = [
                message[i : i + DISCORD_MAX_MESSAGE_LENGTH]
                for i in range(0, len(message), DISCORD_MAX_MESSAGE_LENGTH)
            ]
        else:
            splitChunks = message.split(chr(255))
            chunks = []
            currentChunk = ""
            for chunk in splitChunks:
                if len(currentChunk) + len(chunk) <= DISCORD_MAX_MESSAGE_LENGTH:
                    currentChunk += chunk
                else:
                    chunks.append(currentChunk)
                    currentChunk = chunk
        for chunk in chunks:
            await channel.send(chunk)
