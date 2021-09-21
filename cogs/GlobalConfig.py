import sys, json

class GlobalConfig():
    def __init__(self):
        # Load config file
        self.whitelist = []
        self.trustedRoles = []
        self.logChannelName = ""
        self.moderationChannelName = ""
        self.reportingChannelsList = []
        self.OAuthToken = None
        try:
            f = open('config.json')
            data = json.load(f)
            self.whitelist = data["whitelisted"]
            self.trustedRoles = data["trustedRoles"]
            self.logChannelName = data["logChannel"]
            self.moderationChannelName = data["moderationChannel"]
            self.reportingChannelsList = data["reportingChannels"]
            self.OAuthToken = data["OAuthToken"]
        except:
            print("Error loading config file. Please ensure it matches the specifications")
            sys.exit()

        # Load role menu file
        self.rolemenuData = {}
        try:
            f = open("rolemenu.dat")
            self.rolemenuData = json.load(f)
            f.close()
        except:
            pass

        # Load locked channel data
        self.lockedChannels = []
        try:
            f = open("locked.dat")
            data = json.load(f)
            self.lockedChannels = data["channels"]
            f.close()
        except:
            pass

        self.reactions = "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿".split()

        # Source files cannot be removed and will not show up with a listfiles command, but they can be overwritten
        self.sourceFiles = [".git", ".gitignore", "config.json", "bot.py", "README.md", "Examples", "updatebot.sh", "LICENCE", "locked.dat", "rolemenu.dat"]

        self.permsError = "You don't have permission to use this command"

        # Prepare reporting channels
        self.reportingChannels = {}
        for i in self.reportingChannelsList:
            self.reportingChannels[i[0]] = [i[1], i[2]]

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
