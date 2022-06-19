import json, re
from git import Repo
from cogs.helpers._storage import Storage

DISCORD_MAX_MESSAGE_LENGTH = 2000


class State:
    def __init__(self, logger):
        self.logger = logger
        self.userAllowlist = []
        self.channelAllowlist = []
        self.trustedRoles = [[], [], []]
        self.logChannelName = ""
        self.moderationChannelName = ""
        self.reportingChannelsList = []
        self.reportingChannels = {}
        self.OAuthToken = None
        self.rolemenuData = {}
        self.lockedChannels = {}
        self.registeredTasks = {}
        self.tasksFilepath = ""
        self.reactions = "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿".split()
        self.permsError = "You don't have permission to use this command"
        # Source files cannot be removed and will not show up with a listfiles command, but they can be overwritten
        # The following is only the files not tracked by git. Source files tracked by git are auto generated in the function below
        self.sourceFiles = [
            ".git",
            "config.json",
            "updatebot.sh",
            "locked.dat",
            "rolemenu.dat",
            "tasks.dat",
            "log",
            "Procfile",
            ".profile.d",
            "cogs",
            "LICENCE",
            ".vscode",
            "runtime.txt",
            "requirements.txt",
            ".git-blame-ignore-revs",
            "README.md",
            ".gitignore",
            "examples",
            "contribution guide.md",
            ".heroku",
            "bot.py",
            "config.json.example",
            "tempconfig.json",
        ]

    def generateSourceList(self):
        # TODO Make this work again

        # repo = Repo("./")
        # tree = repo.heads.main.commit.tree
        # files = tree.blobs
        # subdirectories = tree.trees
        # for file in files:
        #     self.sourceFiles.append(file.name)
        # for subdirectory in subdirectories:
        #     self.sourceFiles.append(subdirectory.name)
        pass

    # Parse all configs
    def parseAll(
        self, configFilePath, roleMenuFilePath, lockedChannelFilePath, taskFilePath
    ):
        self._parseConfig(configFilePath)
        self._parseData()

    # Parse main config
    def _parseConfig(self, filePath):
        # Prepare reporting channels
        def prepReportingChannels():
            for i in self.reportingChannelsList:
                self.reportingChannels[i[0]] = [i[1], i[2]]

        try:
            f = open(filePath)
        except Exception as e:
            raise Exception(e)
        try:
            data = json.load(f)
            self.userAllowlist = data["userAllowlist"]
            self.channelAllowlist = data["channelAllowlist"]
            self.trustedRoles = data["trustedRoles"]
            self.logChannelName = data["logChannel"]
            self.moderationChannelName = data["moderationChannel"]
            self.reportingChannelsList = data["reportingChannels"]
            if "OAuthToken" in data:
                self.OAuthToken = data["OAuthToken"]
            prepReportingChannels()
            f.close()
        except Exception as e:
            raise Exception(f"Error: Cannot parse {filePath}: " + str(e))

    # Parse data
    def _parseData(self):
        data = Storage.load(self)
        self.rolemenuData = data["rolemenuData"]
        self.lockedChannels = data["lockedChannels"]
        self.registeredTasks = data["registeredTasks"]

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
