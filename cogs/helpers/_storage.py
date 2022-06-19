import os, json


class Storage:
    def __init__(self, state):
        self.state = state

    def save(self, guildId):
        # TODO find a way of obtaining the guildId here rather than passing as parameter

        data = {}
        data["rolemenuData"] = self.state.rolemenuData
        data["lockedChannels"] = self.state.lockedChannels
        data["registeredTasks"] = self.state.registeredTasks

        if os.environ.get("S3Credentials"):
            # Save to S3
            pass
        else:
            # Local Storage
            f = open(f"{str(guildId)}.dat", "w")
            json.dump(data, f)
            f.close()

    def load(self, guildId):
        # TODO find a way of obtaining the guildId here rather than passing as parameter

        if os.environ.get("S3Credentials"):
            # Save to S3
            return None
        else:
            # Local Storage
            try:
                f = open(f"{str(guildId)}.dat", "w")
                data = json.load(f)
                f.close()
                return data
            except:
                data = {"rolemenuData": {}, "lockedChannels": {}, "registeredTasks": {}}
                f = open(f"{str(guildId)}.dat", "w")
                json.dump(data, f)
                f.close()
                return {data}
