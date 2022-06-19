import discord, json
from discord.ext import commands
from pathlib import Path
from cogs.helpers._storage import Storage


class RoleMenu(commands.Cog):
    def __init__(self, client, state):
        self.client = client
        self.state = state

    def log(self, msg):
        self.state.logger.debug(f"RoleMenu: {msg}")

    # Moderate level authorisation required
    @commands.command("create")
    async def create(self, msg, *args):
        self.log("Create command received")
        if not self.state.checkPerms(
            msg.message.author, level=1
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.state.permsError)
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
            await msg.channel.send(f'Unable to open JSON file "{filename}" :frowning:')
            return

        # Accessing the discord API for this much work takes time so we will keep editing a message along the way to inform the user that it's still doing something
        statusMessage = await msg.channel.send(
            "File loaded successfully! Validating file..."
        )

        # Check if a channel menu already exists - if the -c argument was given then we will overwrite it. Otherwise we will load the one that currently exists
        createNewMenu = True
        channelMenu = {}
        if data["roleMenuChannel"] in self.state.rolemenuData:
            # This seems obsolete to check the flag like this but on the offchance that more flags get introduced to this command later this will ensure it doesn't clash
            if len(args) < 2 or (len(args) > 1 and args[1] != "-c"):
                if any(
                    channel.name == data["roleMenuChannel"]
                    for channel in guild.channels
                ):
                    await statusMessage.edit(
                        content="Role menu already exists, appending to existing menu..."
                    )
                    channelMenu = self.state.rolemenuData[data["roleMenuChannel"]]
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
                del self.state.rolemenuData[data["roleMenuChannel"]]

        ### CREATE CHANNELS ###
        courses = data["courses"]
        for i in courses:
            if len(courses[i]) > 20:
                await statusMessage.edit(
                    content=f"Only 20 courses can exist in a single rolemenu due to reaction limits.\nIssue in {i}. Terminating..."
                )
                return
        await statusMessage.edit(
            content="File loaded successfully! Creating channels..."
        )
        for i in courses:
            await statusMessage.edit(content=f"Creating {i.upper()} channels")
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
                overwriteRole = self.state.getRole(overwriteRoleName, guild)
                if overwriteRole:
                    categoryOverwrites[overwriteRole] = discord.PermissionOverwrite()
                    for customOverwrite in data["customOverwrites"][overwriteRoleName]:
                        try:
                            categoryOverwrites[overwriteRole].__setattr__(
                                customOverwrite[0],
                                overwriteReference[customOverwrite[1]],
                            )
                        except AttributeError:
                            await msg.channel.send(
                                f"Invalid permission name {customOverwrite[0]}. Overwrite not applied"
                            )
                            print(
                                f"Invalid permission name {customOverwrite[0]}. Overwrite not applied"
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
            if i.name in self.state.trustedRoles[0]:
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
            await statusMessage.edit(content=f"Creating {i.upper()} rolemenu")
            # Create message to send
            message = f"​\n**{i.upper()}**\nReact to give yourself a role\n\n"
            currentMenu = {}
            for j in range(len(courses[i])):
                message += f"{self.state.reactions[j]} {courses[i][j].upper()}\n\n"
                currentMenu[self.state.reactions[j]] = courses[i][j].upper()

            menuMessage = await roleMenuChannel.send(message)
            channelMenu[
                str(menuMessage.id)
            ] = currentMenu  # The message id comes in as an integer, but will be serialised as a string when saved to JSON

            # Add reactions
            for j in range(len(courses[i])):
                await menuMessage.add_reaction(self.state.reactions[j])

        self.state.rolemenuData[data["roleMenuChannel"]] = channelMenu
        # Save the file so that if the bot disconnects it will be able to reload
        Storage(self.state).save()
        await statusMessage.edit(content="And that's a wrap! No more work to do")

    # Moderate level authorisation required
    @commands.command("edit")
    async def edit(self, msg, *args):
        self.log("Edit command receieved")
        if not self.state.checkPerms(
            msg.message.author, level=1
        ):  # Check the user has a role in trustedRoles
            await msg.channel.send(self.state.permsError)
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
        for i in self.state.rolemenuData[channelName]:
            tempMsg = await msg.channel.fetch_message(int(i))
            if f"**{args[0]}**" in tempMsg.content:
                editMessage = tempMsg
                rolemenuKey = i
                break
        if editMessage == None:
            await msg.send("Could not find a menu with that name")
            return

        if args[1] == "add":  # Add a new role to an existing role menu
            newReactionIndex = None
            for i in range(len(self.state.reactions)):
                if (
                    self.state.reactions[i]
                    not in self.state.rolemenuData[channelName][rolemenuKey]
                ):
                    newReactionIndex = i
                    break
            if newReactionIndex == None or newReactionIndex >= 20:
                await msg.send("Too many menu items! I can only add 20 reactions!")
                return
            newReaction = self.state.reactions[newReactionIndex]
            await editMessage.edit(
                content=f"{editMessage.content}\n\n{newReaction} {args[2]}\n\n"
            )
            await editMessage.add_reaction(newReaction)
            self.state.rolemenuData[channelName][rolemenuKey][newReaction] = args[2]

            Storage(self.state).save()

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
                content=f"{editMessage.content[:startIndex]}{editMessage.content[endIndex:]}"
            )
            await editMessage.clear_reaction(removeReaction)
            del self.state.rolemenuData[channelName][rolemenuKey][removeReaction]

            Storage(self.state).save()

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
                content=f"{editMessage.content[:startIndex]}{args[3]}{editMessage.content[endIndex:]}"
            )
            reaction = editMessage.content[startIndex - 2 : startIndex - 1]
            self.state.rolemenuData[channelName][rolemenuKey][reaction] = args[3]

            Storage(self.state).save()

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

        if channel.name in self.state.rolemenuData:
            self.log("Reaction add event for role assignment")
            roles = await reaction.member.guild.fetch_roles()
            # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they added and give the user that role
            if (
                str(msg.id) in self.state.rolemenuData[channel.name]
                and msg.author == self.client.user
            ):  # The message id comes in as an integer but is serialised as a string when saved to JSON
                roleName = self.state.rolemenuData[channel.name][str(msg.id)][
                    reaction.emoji.name
                ]
                for i in range(len(roles)):
                    if roles[i].name == roleName:
                        await reaction.member.add_roles(roles[i])

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        # Grab necessary data to analyse the event. A lot of the calls used in reaction_add returns None for reaction_remove
        # because they no longer react to the message so bit of a clunky workaround
        guild = self.client.get_guild(reaction.guild_id)
        member = guild.get_member(reaction.user_id)
        # Ignore reaction remove and add events from itself (when editing the menu)
        if member.bot:
            return
        roles = await guild.fetch_roles()
        channel = self.client.get_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)

        if channel.name in self.state.rolemenuData:
            self.log("Reaction remove event for role assignment")
            # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they removed and remove that role from the user
            if (
                str(msg.id) in self.state.rolemenuData[channel.name]
                and msg.author == self.client.user
            ):  # The message id comes in as an integer but is serialised as a string when saved to JSON
                roleName = self.state.rolemenuData[channel.name][str(msg.id)][
                    reaction.emoji.name
                ]
                for i in range(len(roles)):
                    if roles[i].name == roleName:
                        await member.remove_roles(roles[i])
