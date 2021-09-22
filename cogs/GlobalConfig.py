import json
class GlobalConfig():
    def __init__(self):
        self.whitelist = []
        self.trustedRoles = []
        self.logChannelName = ""
        self.moderationChannelName = ""
        self.reportingChannelsList = []
        self.reportingChannels = {}
        self.OAuthToken = None
        self.rolemenuData = {}
        self.lockedChannels = []   
        self.reactions = "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿".split()
        self.permsError = "You don't have permission to use this command"
        # Source files cannot be removed and will not show up with a listfiles command, but they can be overwritten
        self.sourceFiles = [".git", ".gitignore", "config.json", "bot.py", "README.md", "Examples", "updatebot.sh", "LICENCE", "locked.dat", "rolemenu.dat"]

    # Parse all configs
    def parseAll(self, configFilePath, roleMenuFilePath, lockedChannelFilePath):   
        self._parseConfig(configFilePath)
        self._parseRoleMenuData(roleMenuFilePath)
        self._parseLockedChannelData(lockedChannelFilePath)

    # Parse main config
    def _parseConfig(self, filePath):
        # Prepare reporting channels
        def prepReportingChannels():
            for i in self.reportingChannelsList:
                self.reportingChannels[i[0]] = [i[1], i[2]]
        try:
            f = open(filePath)
            data = json.load(f)
            self.whitelist = data["whitelisted"]
            self.trustedRoles = data["trustedRoles"]
            self.logChannelName = data["logChannel"]
            self.moderationChannelName = data["moderationChannel"]
            self.reportingChannelsList = data["reportingChannels"]
            self.OAuthToken = data["OAuthToken"]
            prepReportingChannels()
            f.close()
        except Exception as e:
            raise Exception(e)

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
            self.lockedChannels = []

    # Only discord users with a role in the trustedRoles list will be allowed to use bot commands    
    def checkPerms(self, msg, author=False):
        if author == True:
            user = msg
        else:
            user = msg.message.author
        roleNames = []
        for i in range(len(user.roles)):
            roleNames.append(user.roles[i].name)
        if any(i in roleNames for i in self.trustedRoles):
            return True
        return False

    def getRole(self, roleName, guild):
        for i in guild.roles:
            if i.name == roleName:
                return i
        return None
