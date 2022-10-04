class GuildState:
    def __init__(self, config, guildId, logger):
        self.guildId = guildId
        self.logger = logger
        self.userAllowlist = (
            config["userAllowlist"] if "userAllowlist" in config else []
        )
        self.channelAllowlist = (
            config["channelAllowlist"] if "channelAllowlist" in config else []
        )
        self.trustedRoles = (
            config["trustedRoles"] if "trustedRoles" in config else [[], [], []]
        )
        self.logChannelName = config["logChannel"] if "logChannel" in config else ""
        self.moderationChannelName = (
            config["moderationChannel"] if "moderationChannel" in config else ""
        )
        self.reportingChannelsList = (
            config["reportingChannels"] if "reportingChannels" in config else []
        )
        self.reportingChannels = {}
        self.rolemenuData = {}
        self.lockedChannels = {}
        self.registeredTasks = {}

        self.prepReportingChannels()

        self._tasksSendTick = False

    # Initialise data
    def initialiseData(self, data):
        self.rolemenuData = data["rolemenuData"]
        self.lockedChannels = data["lockedChannels"]
        self.registeredTasks = data["registeredTasks"]

    def initialiseDefaultData(self):
        self.rolemenuData = {}
        self.lockedChannels = {}
        self.registeredTasks = {}

    def prepReportingChannels(self):
        for i in self.reportingChannelsList:
            self.reportingChannels[i[0]] = [i[1], i[2]]

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
