import discord, os, subprocess, re, sys
from discord.ext import commands
from pathlib import Path
from cogs.helpers._storage import Storage


class FileHandler(commands.Cog):
    def __init__(self, client, state):
        self.client = client
        self.state = state

    def log(self, msg):
        self.state.logger.debug(f"FileHandler: {msg}")

    def findNewFilename(self, filename, prefix=""):
        # Check if the filename has an integer in parentheses like filename(1).dat
        # Don't change the filename if the file doesn't already exist
        if (
            re.match(r".*\(\d+\)\..*", filename) == None
            and Path(f"{prefix}{filename}").is_file()
        ):
            # Separate the filename into two sections
            # The section up to the last decimal
            startMatch = re.match(r".*\.", filename).span()
            start = filename[startMatch[0] : startMatch[1] - 1]
            # The .ext section
            end = filename[startMatch[1] - 1 :]
            # Add a 1 and put it back together
            filename = f"{start}(1){end}"
        while Path(f"{prefix}{filename}").is_file():
            # Separate the filename into three sections.
            # The section up to the opening parenthesis
            startMatch = re.match(r".*\(", filename).span()
            start = filename[startMatch[0] : startMatch[1]]
            # The integer in the middle
            midMatch = re.search(r"\(\d+\)", filename).span()
            mid = filename[midMatch[0] + 1 : midMatch[1] - 1]
            # The closing parenthesis and file extension
            endMatch = re.search(r"\)\..*", filename).span()
            end = filename[endMatch[0] : endMatch[1]]
            # Increment the integer and put it back together
            mid = str(int(mid) + 1)
            filename = f"{start}{mid}{end}"
        return filename

    def saveOldLogFile(self):
        if not Path("log").is_dir():
            os.mkdir("log")
        f = Path("log/rainbowBot.log")
        if f.is_file():
            os.rename(
                f"log/{f.name}", FileHandler.findNewFilename(None, f"log/{f.name}")
            )

    # High level authorisation required
    @commands.command("addfile")
    async def addfile(self, ctx, *args):
        self.log("Add file command received")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        self.state.ensureGuildDirectoryExists(ctx.guild.id)
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        message = ctx.message
        if len(message.attachments) != 1:
            await ctx.send("Please attach a single file to this message")
            return
        filename = message.attachments[0].filename
        if filename in ["updatebot.sh", "bot.py", "temp"]:
            await ctx.send(
                "Due to security risks, this file cannot be changed this way. Please find another way to add it to the cwd"
            )
            return
        f = Path(f"tenants/{ctx.guild.id}/{filename}")
        if f.is_file() and "-o" not in args and "-a" not in args:
            await ctx.send(
                "File already exists. Please specify either -o to overwrite or -a to add a duplicate"
            )
            return
        if len(args) > 1:
            await ctx.send(
                "Please specify a single argument -o to overwrite or -a to add a duplicate"
            )
            return
        if len(args) == 1:
            if args[0] == "-o":
                os.remove(f"tenants/{ctx.guild.id}/{filename}")
            if args[0] == "-a":
                filename = self.findNewFilename(
                    filename, prefix=f"tenants/{ctx.guild.id}/"
                )
                await message.attachments[0].save(
                    f"tenants/{ctx.guild.id}/{filename}",
                    seek_begin=True,
                    use_cached=False,
                )
                await ctx.send(f'File added with filename "{filename}".')
                return
        await message.attachments[0].save(
            f"tenants/{ctx.guild.id}/{filename}",
            seek_begin=True,
            use_cached=False,
        )
        await ctx.send(f'File added with filename "{filename}".')
        self.log(f'Added file with filename "{filename}".')

    # High level authorisation required
    @commands.command("remfile")
    async def remfile(self, ctx, *args):
        self.log("Remove file command received")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        self.state.ensureGuildDirectoryExists(ctx.guild.id)
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        if len(args) != 1:
            await ctx.send("Filename not specified")
        f = Path(f"tenants/{ctx.guild.id}/{args[0]}")
        if (
            not f.is_file()
            or "/" in args[0]
            or "\\" in args[0]
            or args[0] in self.state.sourceFiles
        ):
            await ctx.send("File does not exist")
            return
        os.remove(f"tenants/{ctx.guild.id}/{args[0]}")
        await ctx.send("File removed")

    # High level authorisation required
    @commands.command("listfiles")
    async def listfiles(self, ctx, *args):
        self.log("List files command received")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        self.state.ensureGuildDirectoryExists(ctx.guild.id)
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        message = ""
        for file in os.listdir(f"tenants/{ctx.guild.id}"):
            if file not in self.state.sourceFiles and file != "temp":
                message += f"{file}\n"
        if message == "":
            message = "None"
        await ctx.send(f"Files currently saved are as follows\n\n{message}")

    # High level authorisation required
    @commands.command("update")
    async def update(self, ctx):
        self.log("Update command received")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        f = Path("updatebot.sh")
        if f.is_file():
            subprocess.call(["sh", "./updatebot.sh"])
            sys.exit()
        else:
            await ctx.channel.send("No update script found")
            self.log("Update script not found")

    # High level authorisation required
    @commands.command("addconfig")
    async def addconfig(self, ctx, *args):
        self.log("Add config command received")
        guildState = self.state.guildStates[str(ctx.guild.id)]
        if not guildState.checkPerms(
            ctx.message.author
        ):  # Check the user has a role in trustedRoles
            await ctx.channel.send(self.state.permsError)
            return
        message = ctx.message
        if len(message.attachments) != 1:
            await ctx.send("Please attach a single file to this message")
            return
        filename = message.attachments[0].filename
        if filename != "config.json":
            await ctx.send('File must be named "config.json"')
            return
        await message.attachments[0].save(
            message.attachments[0].filename, seek_begin=True, use_cached=False
        )
        if Storage(self.state).addConfig():
            await ctx.send(f"Config updated!")
            self.log("Config uploaded successfully")
        else:
            await ctx.send(f"Config file upload failed")
            self.log("Config file upload failed")
