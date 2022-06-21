import discord, argparse, logging, os, sys
from discord.ext import commands

# To hold global configuration and variables
from cogs.State import State

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
    await addCogs()
    print("We have logged in as {0.user}".format(client))


# Configure Logging
FileHandler.saveOldLogFile(None)  # Makes log directory if it doesn't already exist
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
logging.getLogger("discord.http").setLevel(logging.INFO)
if os.environ.get("ENVIRONMENT") == "PRODUCTION":
    handler = logging.StreamHandler()
else:
    handler = logging.FileHandler(
        filename="log/rainbowBot.log", encoding="utf-8", mode="w"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    )
logger.addHandler(handler)

# Load the global config which will run some file reads and set default variables
state = State(logger)

# Add each of the cogs, passing in the configuration
async def addCogs():
    await client.add_cog(FileHandler(client, state))
    await client.add_cog(Moderation(client, state))
    await client.add_cog(RoleMenu(client, state))
    await client.add_cog(MessageHandler(client, state))
    await client.add_cog(Tasks(client, state))


# Start bot
if __name__ == "__main__":
    state.generateSourceList()
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
        "--data-file",
        action="store",
        dest="dataFilePath",
        default="data.dat",
        required=False,
        help="File to load data from",
    )
    args = parser.parse_args()

    try:
        state.parseAll(
            args.configFilePath,
            args.dataFilePath,
        )
        token = state.OAuthToken
        if os.environ.get("OAuthToken"):
            token = os.environ.get("OAuthToken")
        if not token:
            print("Invalid OAuthToken")
            sys.exit(1)
        client.run(
            token=token,
            log_handler=handler,
            log_formatter=handler.formatter,
            log_level=logger.level,
        )

        print("Closed")
    except Exception as e:
        print(e)
