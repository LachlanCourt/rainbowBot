import discord, argparse, logging, os, sys, json
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path

# To hold global configuration and variables
from state.State import State

# Import cogs
from cogs.FileHandler import FileHandler
from cogs.Moderation import Moderation
from cogs.RoleMenu import RoleMenu
from cogs.MessageHandler import MessageHandler
from cogs.Tasks import Tasks


dotenv_path = Path(".env")
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Intents give us access to some additional discord moderation features
intents = discord.Intents.all()
client = commands.Bot(command_prefix="$rain", intents=intents)

# Configure Logging
FileHandler.saveOldLogFile(None)  # Makes log directory if it doesn't already exist
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
logging.getLogger("discord.http").setLevel(logging.INFO)
if True:  # os.environ.get("ENVIRONMENT") == "PRODUCTION":
    handler = logging.StreamHandler()
else:
    handler = logging.FileHandler(
        filename="log/rainbowBot.log", encoding="utf-8", mode="w"
    )
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

state = State(client, logger)


@client.event
async def on_ready():
    await state.initialiseGuildStates()

    # Add each of the cogs, passing in the configuration
    await client.add_cog(FileHandler(client, state))
    await client.add_cog(Moderation(client, state))
    await client.add_cog(RoleMenu(client, state))
    await client.add_cog(MessageHandler(client, state))
    await client.add_cog(Tasks(client, state))
    print("Logged in as {0.user}".format(client))


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
        "-D",
        "--data-file",
        action="store",
        dest="dataFilePath",
        default="data.dat",
        required=False,
        help="File to load data from",
    )
    args = parser.parse_args()

    try:
        # state.parseAll(
        #     args.configFilePath,
        #     args.dataFilePath,
        # )
        # token = state.OAuthToken
        token = os.environ.get("OAuthToken")
        if not token:
            print("Invalid OAuthToken")
            sys.exit(1)
        print("Starting up")
        client.run(
            token=token,
            log_handler=handler,
            log_formatter=handler.formatter,
            log_level=logger.level,
        )

        print("Closed")
    except Exception as e:
        print(e)
