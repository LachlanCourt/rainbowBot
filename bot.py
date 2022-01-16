import discord, argparse, logging
from discord.ext import commands

# To hold global configuration and variables
from cogs.GlobalConfig import GlobalConfig

# Import cogs
from cogs.FileHandler import FileHandler
from cogs.Moderation import Moderation
from cogs.RoleMenu import RoleMenu
from cogs.MessageHandler import MessageHandler
from cogs.Tasks import Tasks

# Intents give us access to some additional discord moderation features
intents = discord.Intents.all()
client = commands.Bot(command_prefix="$rain", intents=intents)


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


# Configure Logging
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="rainbowBot.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

# Load the global config which will run some file reads and set default variables
config = GlobalConfig(logger)

# Add each of the cogs, passing in the configuration
client.add_cog(FileHandler(client, config))
client.add_cog(Moderation(client, config))
client.add_cog(RoleMenu(client, config))
client.add_cog(MessageHandler(client, config))
client.add_cog(Tasks(client, config))

# Start bot
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line arguments")
    parser.add_argument(
        "-C",
        "--config-file",
        action="store",
        dest="configFilePath",
        default="config.json",
        required=False,
        help="File to load config from",
    )
    parser.add_argument(
        "-R",
        "--role-file",
        action="store",
        dest="roleMenuFilePath",
        default="rolemenu.dat",
        required=False,
        help="File to load role data from",
    )
    parser.add_argument(
        "-L",
        "--locked-file",
        action="store",
        dest="lockedChannelFilePath",
        default="locked.dat",
        required=False,
        help="File to load locked channel data from",
    )
    parser.add_argument(
        "-T",
        "--task-file",
        action="store",
        dest="taskFilePath",
        default="tasks.dat",
        required=False,
        help="File to load task data from",
    )
    args = parser.parse_args()

    try:
        config.parseAll(
            args.configFilePath,
            args.roleMenuFilePath,
            args.lockedChannelFilePath,
            args.taskFilePath,
        )
        client.run(config.OAuthToken)
        print("Closed")
    except Exception as e:
        print(e)
