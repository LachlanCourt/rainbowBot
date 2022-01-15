import discord, json
from discord.ext import commands
from pathlib import Path


class RoleMenu(commands.Cog):
    def __init__(self, client, config):
        self.client = client
        self.config = config

    # Moderate level authorisation required
    @commands.command("create")
    async def create(self, msg, *args):
        if not self.config.checkPerms(
            msg.message.author, level=1
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.config.permsError)
            return
        if len(args) == 0:  # Check for correct argument
            await msg.channel.send(
                "Please specify the filename of a JSON file to load from"
            )
            return

        guild = msg.guild
        filename = args[0]
        if not filename.endswith(".json"):
            filename += ".json"
        try:
            f = open(filename)
            data = json.load(f)
            f.close()
        except:
            await msg.channel.send(
                'Unable to open JSON file "' + filename + '" :frowning:'
            )
            return

        # Accessing the discord API for this much work takes time so we will keep editing a message along the way to inform the user that it's still doing something
        statusMessage = await msg.channel.send(
            "File loaded successfully! Validating file..."
        )
        self.config.rolemenuData = {}
        # If a rolemenu.dat file exists, load the existing rolemenu data
        try:
            f = open("rolemenu.dat")
            self.config.rolemenuData = json.load(f)
            f.close()
        except:
            await statusMessage.edit(content="Creating new rolemenu file...")

        # Check if a channel menu already exists - if the -c argument was given then we will overwrite it. Otherwise we will load the one that currently exists
        createNewMenu = True
        channelMenu = {}
        if data["roleMenuChannel"] in self.config.rolemenuData:
            # This seems obsolete to check the flag like this but on the offchance that more flags get introduced to this command later this will ensure it doesn't clash
            if len(args) < 2 or (len(args) > 1 and args[1] != "-c"):
                if any(
                    channel.name == data["roleMenuChannel"]
                    for channel in guild.channels
                ):
                    await statusMessage.edit(
                        content="Role menu already exists, appending to existing menu..."
                    )
                    channelMenu = self.config.rolemenuData[data["roleMenuChannel"]]
                    createNewMenu = False
                else:
                    await statusMessage.edit(
                        content="A role menu exists for the specified channel but the channel appears to be deleted or inaccessible. Run again with -c to clear the old menu or check my permissions. Terminating..."
                    )
                    return
            if len(args) > 1 and args[1] == "-c":
                await statusMessage.edit(
                    content="-c flag included, clearing old role menu..."
                )
                # Further down when generating the role menu, the decision to make a new channel or not is made by seeing whether a menu exists in rolemenuData
                # If we are clearing with the -c argument we should clear the old menu from rolemenuData
                del self.config.rolemenuData[data["roleMenuChannel"]]

        ### CREATE CHANNELS ###
        courses = data["courses"]
        for i in courses:
            if len(courses[i]) > 20:
                await statusMessage.edit(
                    content="Only 20 courses can exist in a single rolemenu due to reaction limits.\nIssue in "
                    + i
                    + ". Terminating..."
                )
                return
        await statusMessage.edit(
            content="File loaded successfully! Creating channels..."
        )
        for i in courses:
            await statusMessage.edit(content="Creating " + i.upper() + " channels")
            # Create roles and record roles for overwrites
            roleObjs = []
            for j in range(len(courses[i])):
                role = await guild.create_role(
                    name=courses[i][j].upper(), colour=255
                )  # Convert HEX code to integer (Bc that makes sense??) this is blue #0000ff
                roleObjs.append(role)

            # Create category overwrites and disable to @everyone by default
            categoryOverwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False)
            }

            # Find and generate custom overwrites for category and channel simultaneously
            overwriteReference = {-1: False, 0: None, 1: True}
            customChannelOverwrites = {}
            for overwriteRoleName in data["customOverwrites"]:
                overwriteRole = self.config.getRole(overwriteRoleName, guild)
                if overwriteRole:
                    categoryOverwrites[overwriteRole] = discord.PermissionOverwrite()
                    for customOverwrite in data["customOverwrites"][overwriteRoleName]:
                        categoryOverwrites[overwriteRole].__setattr__(
                            customOverwrite[0], overwriteReference[customOverwrite[1]]
                        )
                    customChannelOverwrites[overwriteRole] = categoryOverwrites[
                        overwriteRole
                    ]

            # Add view channel permission to the role specific to that channel
            for j in range(len(roleObjs)):
                categoryOverwrites[roleObjs[j]] = discord.PermissionOverwrite(
                    view_channel=True
                )

            # Create category and apply overwrites
            category = await guild.create_category(
                name=i.upper(), overwrites=categoryOverwrites
            )

            # Create channels and apply overwrites
            for j in range(len(courses[i])):
                channelOverwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    roleObjs[j]: discord.PermissionOverwrite(view_channel=True),
                }
                for customOverwriteRole in customChannelOverwrites:
                    channelOverwrites[customOverwriteRole] = customChannelOverwrites[
                        customOverwriteRole
                    ]
                await guild.create_text_channel(
                    name=courses[i][j], category=category, overwrites=channelOverwrites
                )

            # Create voice channel and apply category overwrites
            await guild.create_voice_channel(
                i.upper(), overwrites=categoryOverwrites, category=category
            )
        await statusMessage.edit(
            content="Course channels created! Generating role menu channel..."
        )

        ### CREATE ROLE MENU ###
        roleMenuOverwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False, send_messages=False, add_reactions=False
            )
        }
        for i in guild.roles:
            if i.name in self.config.trustedRoles:
                roleMenuOverwrites[i] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )
        if createNewMenu:
            roleMenuChannel = await guild.create_text_channel(
                name=data["roleMenuChannel"], overwrites=roleMenuOverwrites, position=0
            )  # Role menu will jump to the top of channel list and you can move it from there
            await statusMessage.edit(
                content="Role menu channel created! Generating menu..."
            )
        else:
            await statusMessage.edit(
                content="Role menu channel found! Generating menu..."
            )
            for i in guild.channels:
                if i.name == data["roleMenuChannel"]:
                    roleMenuChannel = i

        if createNewMenu:
            await roleMenuChannel.send(
                "Welcome to the course selection channel! React to a message below to gain access to a text channel for that subject"
            )

        for i in courses:
            await statusMessage.edit(content="Creating " + i.upper() + " rolemenu")
            # Create message to send
            message = "​\n**" + i.upper() + "**\nReact to give yourself a role\n\n"
            currentMenu = {}
            for j in range(len(courses[i])):
                message += (
                    self.config.reactions[j] + " " + courses[i][j].upper() + "\n\n"
                )
                currentMenu[self.config.reactions[j]] = courses[i][j].upper()

            menuMessage = await roleMenuChannel.send(message)
            channelMenu[
                str(menuMessage.id)
            ] = currentMenu  # The message id comes in as an integer, but will be serialised as a string when saved to JSON

            # Add reactions
            for j in range(len(courses[i])):
                await menuMessage.add_reaction(self.config.reactions[j])

        self.config.rolemenuData[data["roleMenuChannel"]] = channelMenu
        # Save the file so that if the bot disconnects it will be able to reload
        f = open("rolemenu.dat", "w")
        json.dump(self.config.rolemenuData, f)
        f.close()
        await statusMessage.edit(content="And that's a wrap! No more work to do")

    # Moderate level authorisation required
    @commands.command("edit")
    async def edit(self, msg, *args):
        if not self.config.checkPerms(
            msg.message.author, level=1
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.config.permsError)
            return
        if len(args) < 3 or len(args) > 4:
            await msg.send(
                "Incorrect number of arguments!\nUsage: <menuName> <add/remove/update> <roleName> [<newRoleName>]"
            )
            return
        channelName = msg.channel.name
        # Find message to edit
        editMessage = None
        rolemenuKey = None
        for i in self.config.rolemenuData[channelName]:
            tempMsg = await msg.channel.fetch_message(int(i))
            if "**" + args[0] + "**" in tempMsg.content:
                editMessage = tempMsg
                rolemenuKey = i
                break
        if editMessage == None:
            await msg.send("Could not find a menu with that name")
            return

        if args[1] == "add":  # Add a new role to an existing role menu
            newReactionIndex = None
            for i in range(len(self.config.reactions)):
                if (
                    self.config.reactions[i]
                    not in self.config.rolemenuData[channelName][rolemenuKey]
                ):
                    newReactionIndex = i
                    break
            if newReactionIndex == None or newReactionIndex >= 20:
                await msg.send("Too many menu items! I can only add 20 reactions!")
                return
            newReaction = self.config.reactions[newReactionIndex]
            await editMessage.edit(
                content=editMessage.content
                + "\n\n"
                + newReaction
                + " "
                + args[2]
                + "\n\n"
            )
            await editMessage.add_reaction(newReaction)
            self.config.rolemenuData[channelName][rolemenuKey][newReaction] = args[2]

            f = open("rolemenu.dat", "w")
            json.dump(self.config.rolemenuData, f)
            f.close()

            await msg.send("Role added successfully")
            return

        if args[1] == "remove":  # Remove a role from an existing role menu
            if args[2] not in editMessage.content:
                await msg.send("That role does not exist in this menu")
                return
            for i in editMessage.content:
                startIndex = editMessage.content.find(args[2])
                endIndex = startIndex + len(args[2])
                startIndex -= 4  # Allow for the reaction and the space between the reaction and the role name
            removeReaction = editMessage.content[startIndex + 2 : startIndex + 3]
            await editMessage.edit(
                content=editMessage.content[:startIndex]
                + editMessage.content[endIndex:]
            )
            await editMessage.clear_reaction(removeReaction)
            del self.config.rolemenuData[channelName][rolemenuKey][removeReaction]

            f = open("rolemenu.dat", "w")
            json.dump(self.config.rolemenuData, f)
            f.close()

            await msg.send("Role removed successfully")
            return

        if (
            args[1] == "update"
        ):  # Update a role in an existing role menu (Change spelling etc.)
            if args[2] not in editMessage.content:
                await msg.send("That role does not exist in this menu")
                return
            if len(args) < 4:
                await msg.send("Please specify the value to change the role to")
                return
            for i in editMessage.content:
                startIndex = editMessage.content.find(args[2])
                endIndex = startIndex + len(args[2])
            await editMessage.edit(
                content=editMessage.content[:startIndex]
                + args[3]
                + editMessage.content[endIndex:]
            )
            reaction = editMessage.content[startIndex - 2 : startIndex - 1]
            self.config.rolemenuData[channelName][rolemenuKey][reaction] = args[3]

            f = open("rolemenu.dat", "w")
            json.dump(self.config.rolemenuData, f)
            f.close()

            await msg.send("Role updated successfully")
            return

        # The three valid commands return at the end of them
        await msg.send("Could not process your request! Check your spelling...")

    # Reaction add event specific to assigning roles in Role Menu
    # For the reaction add event regarding channel locking, check Moderation cog
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if (
            reaction.member.bot
        ):  # Ignore reaction remove and add events from itself (when editing the menu)
            return

        # Grab necessary data to analyse the event
        channel = self.client.get_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)

        if channel.name in self.config.rolemenuData:
            roles = await reaction.member.guild.fetch_roles()
            # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they added and give the user that role
            if (
                str(msg.id) in self.config.rolemenuData[channel.name]
                and msg.author == self.client.user
            ):  # The message id comes in as an integer but is serialised as a string when saved to JSON
                roleName = self.config.rolemenuData[channel.name][str(msg.id)][
                    reaction.emoji.name
                ]
                for i in range(len(roles)):
                    if roles[i].name == roleName:
                        await reaction.member.add_roles(roles[i])

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        # Grab necessary data to analyse the event. A lot of the calls used in reaction_add returns null for reaction_remove
        # because they no longer react to the message so bit of a clunky workaround
        guild = self.client.get_guild(reaction.guild_id)
        member = guild.get_member(reaction.user_id)
        # Ignore reaction remove and add events from itself (when editing the menu)
        if member.bot:
            return
        roles = await guild.fetch_roles()
        channel = self.client.get_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)

        if channel.name in self.config.rolemenuData:
            # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they removed and remove that role from the user
            if (
                str(msg.id) in self.config.rolemenuData[channel.name]
                and msg.author == self.client.user
            ):  # The message id comes in as an integer but is serialised as a string when saved to JSON
                roleName = self.config.rolemenuData[channel.name][str(msg.id)][
                    reaction.emoji.name
                ]
                for i in range(len(roles)):
                    if roles[i].name == roleName:
                        await member.remove_roles(roles[i])
