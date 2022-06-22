import json, re, os
from cogs.helpers._storage import Storage


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
        self.logChannelName = (
            config["logChannelName"] if "logChannelName" in config else ""
        )
        self.moderationChannelName = (
            config["moderationChannelName"] if "moderationChannelName" in config else ""
        )
        self.reportingChannelsList = (
            config["reportingChannelsList"] if "reportingChannelsList" in config else []
        )
        self.reportingChannels = (
            config["reportingChannels"] if "reportingChannels" in config else {}
        )

        self.rolemenuData = {}
        self.lockedChannels = {}
        self.registeredTasks = {}

    # Initialise data
    def initialiseData(self, data):
        self.rolemenuData = data["rolemenuData"]
        self.lockedChannels = data["lockedChannels"]
        self.registeredTasks = data["registeredTasks"]
