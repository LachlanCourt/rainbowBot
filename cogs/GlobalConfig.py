import json


class GlobalConfig:
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
        self.sourceFiles = [
            ".git",
            ".gitignore",
            "config.json",
            "bot.py",
            "README.md",
            "Examples",
            "updatebot.sh",
            "LICENCE",
            "locked.dat",
            "rolemenu.dat",
        ]

    # Parse all configs
    def parseAll(
        self, configFilePath, roleMenuFilePath, lockedChannelFilePath, taskFilePath
    ):
        self._parseConfig(configFilePath)
        self._parseRoleMenuData(roleMenuFilePath)
        self._parseLockedChannelData(lockedChannelFilePath)
        self._parseTaskData(taskFilePath)

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
            self.OAuthToken = data["OAuthToken"]
            prepReportingChannels()
            f.close()
        except Exception as e:
            raise Exception(f"Error: Cannot parse {filePath}: " + str(e))

    # Parse role menu data
    def _parseRoleMenuData(self, filePath):
        try:
            f = open(filePath)
            self.rolemenuData = json.load(f)
            f.close()
        except Exception:
            self.rolemenuData = {}

    # Parse locked channel data
    def _parseLockedChannelData(self, filePath):
        try:
            f = open(filePath)
            data = json.load(f)
            self.lockedChannels = data["channels"]
            f.close()
        except Exception:
            self.lockedChannels = {}

    # Parse task data
    def _parseTaskData(self, filePath):
        self.tasksFilepath = filePath
        try:
            f = open(filePath)
            data = json.load(f)
            self.registeredTasks = data["registeredTasks"]
            f.close()
        except Exception:
            self.registeredTasks = {}

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

    def getRole(self, roleName, guild):
        for i in guild.roles:
            if i.name == roleName:
                return i
        return None
