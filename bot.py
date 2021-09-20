import discord, json, sys, os, subprocess, re
from discord.ext import commands
from pathlib import Path

# Intents give us access to some additional discord moderation features
intents = discord.Intents.all()
client = commands.Bot(command_prefix="$rain", intents=intents)

# Load config file
whitelist = []
trustedRoles = []
logChannelName = ""
moderationChannelName = ""
reportingChannelsList = []
OAuthToken = None
try:
    f = open('config.json')
    data = json.load(f)
    whitelist = data["whitelisted"]
    trustedRoles = data["trustedRoles"]
    logChannelName = data["logChannel"]
    moderationChannelName = data["moderationChannel"]
    reportingChannelsList = data["reportingChannels"]
    OAuthToken = data["OAuthToken"]
except:
    print("Error loading config file. Please ensure it matches the specifications")
    sys.exit()

# Load role menu file
rolemenuData = {}
try:
    f = open("rolemenu.dat")
    rolemenuData = json.load(f)
    f.close()
except:
    pass

# Load locked channel data
try:
    f = open("locked.dat")
    data = json.load(f)
    lockedChannels = data["channels"]
    f.close()
except:
    lockedChannels = []

reactions = "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿".split()

# Source files cannot be removed and will not show up with a listfiles command, but they can be overwritten
sourceFiles = [".git", ".gitignore", "config.json", "bot.py", "README.md", "Examples", "updatebot.sh", "LICENCE", "locked.dat", "rolemenu.dat"]

permsError = "You don't have permission to use this command"

# Prepare reporting channels
reportingChannels = {}
for i in reportingChannelsList:
    reportingChannels[i[0]] = [i[1], i[2]]

# Only discord users with a role in the trustedRoles list will be allowed to use bot commands    
def checkPerms(msg, author=False):
    if author == True:
        user = msg
    else:
        user = msg.message.author
    roleNames = []
    for i in range(len(user.roles)):
        roleNames.append(user.roles[i].name)
    if any(i in roleNames for i in trustedRoles):
        return True
    return False

def getRole(roleName, guild):
    for i in guild.roles:
        if i.name == roleName:
            return i
    return None
    

def findNewFilename(filename):
    # Check if the filename has an integer in parentheses like filename(1).dat
    # Don't change the filename if the file doesn't already exist
    if re.match(r".*\(\d+\)\..*", filename) == None and Path(filename).is_file(): 
        # Separate the filename into two sections
        # The section up to the last decimal
        startMatch = re.match(r".*\.", filename).span()
        start = filename[startMatch[0]:startMatch[1] - 1]
        # The .ext section
        end = filename[startMatch[1] - 1:]
        # Add a 1 and put it back together
        filename = start + "(1)" + end
    while Path(filename).is_file():
        # Separate the filename into three sections.
        # The section up to the opening parenthesis
        startMatch = re.match(r".*\(", filename).span()
        start = filename[startMatch[0]:startMatch[1]]
        # The integer in the middle
        midMatch = re.search(r"\(\d+\)", filename).span()
        mid = filename[midMatch[0] + 1:midMatch[1] - 1]
        # The closing parenthesis and file extension
        endMatch = re.search(r"\)\..*", filename).span()
        end = filename[endMatch[0]:endMatch[1]]
        # Increment the integer and put it back together
        mid = str(int(mid) + 1)
        filename = start + mid + end
    return filename

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    # Don't handle messages from ourself
    if message.author == client.user:
        return
    # Messages that have been sent as a direct message to the bot will be reposted in the channel specified in logChannel
    if message.channel.type == discord.ChannelType.private:
        if logChannelName == "": # Handle gracefully if no channel is specified to send a DM
            await message.channel.send("I am not set up to receive direct messages, please contact your server administrators another way!")
            return
        await message.channel.send("Thankyou for your message, it has been passed on to the administrators")
        guilds = message.author.mutual_guilds
        for guild in guilds:
            logChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=logChannelName)
            await logChannel.send(message.author.mention + " sent a direct message, they said\n\n" + message.content)
    # Messages that are sent into a channel specified in reportingChannels will be deleted and reposted in the specified reporting log with the custom message
    if message.channel.type != discord.ChannelType.private and message.channel.name in reportingChannels and message.author.name not in whitelist:
        await message.delete(delay=None)
        channel = discord.utils.get(client.get_all_channels(), guild__name=message.guild.name, name=reportingChannels[message.channel.name][0])
        replyMessage = reportingChannels[message.channel.name][1]
        replyMessage = replyMessage.replace("@user", message.author.mention)
        replyMessage = replyMessage.replace("@message", message.content)
        # If there are multiple different role mentions discord replaces each with <@38473847387837> and we want to ignore these
        # The following matches if an @ symbol is not proceeded by a < symbol, and then matches any number of characters up until the first $ symbol
        matchString = r"(?<!\<)@.*?\$"
        while re.search(matchString, replyMessage) != None:
            roleNameIndex = re.search(matchString, replyMessage).span()
            roleName = replyMessage[roleNameIndex[0] + 1:roleNameIndex[1] - 1]
            role = getRole(roleName, message.guild)
            if role != None: # Only replace if the role actually exists. If not, keep searching through replyMessage
                replyMessage = replyMessage.replace(f"@{roleName}$", role.mention)               
        await channel.send(replyMessage)
    # Now that the response to any message has been handled, process the official commands
    await client.process_commands(message)

@client.event
async def on_raw_message_delete(rawMessage):
    guild = client.get_guild(rawMessage.guild_id)
    channel = client.get_channel(rawMessage.channel_id)
    # If the message was sent before the bot was logged on, it is unfortunately innaccessible. Ignore also if the author is on the whitelist or if the channel is locked (The lock channel command deletes the message of the sender automatically)
    if not rawMessage.cached_message or channel.name in reportingChannels or rawMessage.cached_message.author.name in whitelist or channel.name in lockedChannels:
        return    
    message = rawMessage.cached_message
    member = guild.get_member(message.author.id)
    # Ignore deleted messages if the member no longer exists, they are a bot, or if this functionality is disabled 
    if member == None or member.bot or moderationChannelName == "":
        return
    moderationChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=moderationChannelName)
    
    # People with trusted roles will likely have access to the log channel for deleted messages
    # Getting a ping every time might get annoying, so don't ping people with trusted roles.
    user = message.author.mention
    if checkPerms(message.author, author=True):
        user = message.author.name
        
    if len(message.attachments) == 0: # There are no attachments, it was just text
        await moderationChannel.send(user + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content)
    else: #There was an attachment
        if message.content != "":
            await moderationChannel.send(user + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content + "\n\nAnd had the following attachment(s)")
        else:
            await moderationChannel.send(user + " deleted a message in " + message.channel.mention + ". The message consisted of the following attachement(s)")
        for i in message.attachments:
            # The cached attachment URL becomes invalid after a few minutes. The following ensures valid media is accessible for moderation purposes
            await i.save(i.filename, seek_begin=True, use_cached=False) # Save the media locally from the cached URL before it becomes invalid
            file = discord.File(fp=i.filename,) # Create a discord file object based on this saved media
            await moderationChannel.send(content=None,file=file) # Reupload the media to the log channel
            os.remove(i.filename) # Remove the local download of the media
            
@client.event
async def on_raw_message_edit(rawMessage):
    # If the message was sent before the bot was logged on, it is unfortunately innaccessible. Ignore also if the author is on the whitelist
    if not rawMessage.cached_message or rawMessage.cached_message.author.name in whitelist:
        return
    guild = client.get_guild(rawMessage.cached_message.author.guild.id)
    channel = client.get_channel(rawMessage.channel_id)
    member = guild.get_member(rawMessage.cached_message.author.id)

    # Ignore deleted messages if the member no longer exists, they are a bot, or if this functionality is disabled 
    if member == None or member.bot or moderationChannelName == "":
        return

    # Try and grab the data of the message and any attachments
    before = rawMessage.cached_message.content
    try:
        after = rawMessage.data["content"]
    except:
        return
    beforeAttach = rawMessage.cached_message.attachments
    afterAttach = rawMessage.data["attachments"]

    #Pinning a message triggers an edit event. Ignore it
    if before == after and len(beforeAttach) == len(afterAttach):
        return

    # Inform the moderation team
    moderationChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=moderationChannelName)
    if before == "":
        before = "<<No message content>>"
    if after == "":
        after = "<<No message content>>"

    # People with trusted roles will likely have access to the log channel for edited messages
    # Getting a ping every time might get annoying, so don't ping people with trusted roles.
    user = rawMessage.cached_message.author.mention
    if checkPerms(rawMessage.cached_message.author, author=True):
        user = rawMessage.cached_message.author.name
    await moderationChannel.send(user + " just edited their message in " + channel.mention + ", they changed their original message which said \n\n" + before + "\n\nTo a new message saying \n\n" + after)

    if len(rawMessage.cached_message.attachments) != len(rawMessage.data["attachments"]):
        await moderationChannel.send("They also changed the attachments as follows. Before: ")
        for i in beforeAttach: # See message delete function for details of the following
            await i.save(i.filename, seek_begin=True, use_cached=False)
            file = discord.File(fp=i.filename,)
            await moderationChannel.send(content=None,file=file)
            os.remove(i.filename)
        await moderationChannel.send("After:")
        for i in afterAttach:
            await i.save(i.filename, seek_begin=True, use_cached=False)
            file = discord.File(fp=i.filename,)
            await moderationChannel.send(content=None,file=file)
            os.remove(i.filename)

@client.event
async def on_raw_reaction_add(reaction):
    if reaction.member.bot: # Ignore reaction remove and add events from itself (when editing the menu)
        return
    
    # Grab necessary data to analyse the event
    channel = client.get_channel(reaction.channel_id)
    msg = await channel.fetch_message(reaction.message_id)

    # Check first if the reaction is for a channel that is currently locked
    if channel.name in lockedChannels:
        roleName = msg.channel.name.upper()
        guild = channel.guild
        
        role = None
        for i in guild.roles:
            if i.name == roleName:
                role = i

        if role == None:
            return
        if reaction.emoji.name == "🔓" and checkPerms(reaction.member, author=True):
            await msg.channel.set_permissions(role, read_messages=True, send_messages=None)
            lockedChannels.remove(msg.channel.name)
            data = {'channels':lockedChannels}

            await msg.delete(delay=None)

            f = open("locked.dat", "w")
            json.dump(data, f)
            f.close()
            return
    
    roles = await reaction.member.guild.fetch_roles()
    # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they added and give the user that role
    if str(msg.id) in rolemenuData[channel.name] and msg.author == client.user: # The message id comes in as an integer but is serialised as a string when saved to JSON
        roleName = rolemenuData[channel.name][str(msg.id)][reaction.emoji.name]
        for i in range(len(roles)):
            if roles[i].name == roleName:
                await reaction.member.add_roles(roles[i])

@client.event
async def on_raw_reaction_remove(reaction):
    # Grab necessary data to analyse the event. A lot of the calls used in reaction_add returns null for reaction_remove
    # because they no longer react to the message so bit of a clunky workaround
    guild = client.get_guild(reaction.guild_id)
    member = guild.get_member(reaction.user_id)
    # Ignore reaction remove and add events from itself (when editing the menu)
    if member.bot:
        return
    roles = await guild.fetch_roles()
    channel = client.get_channel(reaction.channel_id)
    msg = await channel.fetch_message(reaction.message_id)

    # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they removed and remove that role from the user
    if str(msg.id) in rolemenuData[channel.name] and msg.author == client.user: # The message id comes in as an integer but is serialised as a string when saved to JSON
        roleName = rolemenuData[channel.name][str(msg.id)][reaction.emoji.name]
        for i in range(len(roles)):
            if roles[i].name == roleName:
                await member.remove_roles(roles[i])

##### ROLE MENU #####

@client.command("create")
async def create(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return
    if len(args) == 0: # Check for correct argument
        await msg.channel.send("Please specify the filename of a JSON file to load from")
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
        await msg.channel.send('Unable to open JSON file "' + filename + '" :frowning:')
        return

    # Accessing the discord API for this much work takes time so we will keep editing a message along the way to inform the user that it's still doing something
    statusMessage = await msg.channel.send("File loaded successfully! Validating file...")
    global rolemenuData
    rolemenuData = {}
    # If a rolemenu.dat file exists, load the existing rolemenu data
    try:
        f = open("rolemenu.dat")
        #global rolemenuData
        rolemenuData = json.load(f)
        f.close()
    except:
        await statusMessage.edit(content="Creating new rolemenu file...")
       
    # Check if a channel menu already exists - if the -c argument was given then we will overwrite it. Otherwise we will load the one that currently exists
    createNewMenu = True
    channelMenu = {}
    if data["roleMenuChannel"] in rolemenuData:
        # This seems obsolete to check the flag like this but on the offchance that more flags get introduced to this command later this will ensure it doesn't clash
        if len(args) < 2 or len(args) > 1 and args[1] != "-c":
            await statusMessage.edit(content="Role Menu already exists, appending to existing menu...")
            channelMenu = rolemenuData[data["roleMenuChannel"]]
            createNewMenu = False
    
    # Find sinbin role
    sinbinRole = None
    for i in guild.roles:
        if i.name == data["sinbinRole"]:
            sinbinRole = i

    ### CREATE CHANNELS ###
    courses = data["courses"]
    for i in courses:
        if len(courses[i]) > 20:
            await statusMessage.edit(content="Only 20 courses can exist in a single rolemenu due to reaction limits.\nIssue in " + i + ". Terminating...")
            return
    await statusMessage.edit(content="File loaded successfully! Creating channels...")
    for i in courses:
        await statusMessage.edit(content="Creating " + i.upper() + " channels")
        # Create roles and record roles for overwrites
        roleObjs = []
        for j in range(len(courses[i])):
            role = await guild.create_role(name=courses[i][j].upper(), colour=255)# Convert HEX code to integer (Bc that makes sense??) this is blue #0000ff
            roleObjs.append(role)
            
        # Create category overwrites and disable to @everyone by default
        categoryOverwrites = {guild.default_role:discord.PermissionOverwrite(view_channel=False)}
        if sinbinRole != None:
            categoryOverwrites[sinbinRole] = discord.PermissionOverwrite(send_messages=False, add_reactions=False, connect=False)
        for j in range(len(roleObjs)):
            categoryOverwrites[roleObjs[j]] = discord.PermissionOverwrite(view_channel=True)
                               
        # Create category and apply overwrites
        category = await guild.create_category(name=i.upper(), overwrites=categoryOverwrites)
                               
        # Create channels and apply overwrites
        for j in range(len(courses[i])):
            channelOverwrites = {
                guild.default_role:discord.PermissionOverwrite(view_channel=False),
                roleObjs[j]:discord.PermissionOverwrite(view_channel=True)
            }
            if sinbinRole != None:
                channelOverwrites[sinbinRole] = discord.PermissionOverwrite(send_messages=False, add_reactions=False)
            await guild.create_text_channel(name=courses[i][j], category=category, overwrites=channelOverwrites)
            
        # Create voice channel and apply category overwrites
        await guild.create_voice_channel(i.upper(), overwrites=categoryOverwrites, category=category)
    await statusMessage.edit(content="Course channels created! Generating role menu channel...")

    ### CREATE ROLE MENU ###
    roleMenuOverwrites = {guild.default_role:discord.PermissionOverwrite(view_channel=False, send_messages=False, add_reactions=False)}
    for i in guild.roles:
        if i.name in trustedRoles:
            roleMenuOverwrites[i] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    if createNewMenu:
        roleMenuChannel = await guild.create_text_channel(name=data["roleMenuChannel"], overwrites=roleMenuOverwrites, position=0) # Role menu will jump to the top of channel list and you can move it from there
        await statusMessage.edit(content="Role menu channel created! Generating menu...")
    else:
        await statusMessage.edit(content="Role menu channel found! Generating menu...")
        #pass ????
        # I don't think I need this but I don't want to remove it yet just in case
        for i in guild.channels: #
            if i.name == data["roleMenuChannel"]: #
                roleMenuChannel = i #
    
    if createNewMenu:
        await roleMenuChannel.send("Welcome to the course selection channel! React to a message below to gain access to a text channel for that subject")

    for i in courses:
        await statusMessage.edit(content="Creating " + i.upper() + " rolemenu")
        # Create message to send
        message = "​\n**" + i.upper() + "**\nReact to give yourself a role\n\n"
        currentMenu = {}
        for j in range(len(courses[i])):
            message += reactions[j] + " " + courses[i][j].upper() + "\n\n"
            currentMenu[reactions[j]] = courses[i][j].upper()
            
        menuMessage = await roleMenuChannel.send(message)
        channelMenu[str(menuMessage.id)] = currentMenu # The message id comes in as an integer, but will be serialised as a string when saved to JSON

        # Add reactions
        for j in range(len(courses[i])):
            await menuMessage.add_reaction(reactions[j])

    rolemenuData[data["roleMenuChannel"]] = channelMenu
    # Save the file so that if the bot disconnects it will be able to reload                               
    f = open("rolemenu.dat", "w")
    json.dump(rolemenuData, f)
    f.close()
    await statusMessage.edit(content="And that's a wrap! No more work to do")

@client.command("edit")
async def edit(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return
    if len(args) < 3 or len(args) > 4:
        await msg.send("Incorrect number of arguments!\nUsage: <menuName> <add/remove/update> <roleName> [<newRoleName>]")
        return
    # Find message to edit
    editMessage = None
    rolemenuKey = None
    for i in rolemenuData:
        tempMsg = await msg.channel.fetch_message(int(i))
        if "**" + args[0] + "**" in tempMsg.content:
            editMessage = tempMsg
            rolemenuKey = i
            break    
    if editMessage == None:
        await msg.send("Could not find a menu with that name")
        return

    if args[1] == "add": # Add a new role to an existing role menu
        newReactionIndex = None
        for i in range(len(reactions)):
            if reactions[i] not in rolemenuData[rolemenuKey]:
                newReactionIndex = i
                break
        if newReactionIndex == None or newReactionIndex >= 20:
            await msg.send("Too many menu items! I can only add 20 reactions!")
            return
        newReaction = reactions[newReactionIndex]
        await editMessage.edit(content=editMessage.content + "\n\n" + newReaction + " " + args[2] + "\n\n")
        await editMessage.add_reaction(newReaction)
        rolemenuData[rolemenuKey][newReaction] = args[2]
        
        f = open("rolemenu.dat", "w")
        json.dump(rolemenuData, f)
        f.close()
        
        await msg.send("Role added successfully")
        return

    if args[1] == "remove": # Remove a role from an existing role menu
        if args[2] not in editMessage.content:
            await msg.send("That role does not exist in this menu")
            return
        for i in editMessage.content:
            startIndex = editMessage.content.find(args[2])
            endIndex = startIndex + len(args[2])
            startIndex -= 4 # Allow for the reaction and the space between the reaction and the role name
        removeReaction = editMessage.content[startIndex + 2:startIndex + 3]
        await editMessage.edit(content=editMessage.content[:startIndex] + editMessage.content[endIndex:])
        await editMessage.clear_reaction(removeReaction)
        del(rolemenuData[rolemenuKey][removeReaction])

        f = open("rolemenu.dat", "w")
        json.dump(rolemenuData, f)
        f.close()
        
        await msg.send("Role removed successfully")
        return

    if args[1] == "update": # Update a role in an existing role menu (Change spelling etc.)
        if args[2] not in editMessage.content:
            await msg.send("That role does not exist in this menu")
            return
        if len(args) < 4:
            await msg.send("Please specify the value to change the role to")
            return
        for i in editMessage.content:
            startIndex = editMessage.content.find(args[2])
            endIndex = startIndex + len(args[2])
        await editMessage.edit(content=editMessage.content[:startIndex] + args[3] + editMessage.content[endIndex:])
        reaction = editMessage.content[startIndex - 2:startIndex - 1]
        rolemenuData[rolemenuKey][reaction] = args[3]

        f = open("rolemenu.dat", "w")
        json.dump(rolemenuData, f)
        f.close()
        
        await msg.send("Role updated successfully")
        return

    # The three valid commands return at the end of them
    await msg.send("Could not process your request! Check your spelling...")

@client.command("update")
async def update(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return
    f = Path("updatebot.sh")
    if f.is_file():
        subprocess.call(['sh', './updatebot.sh'])
        sys.exit()
    else:
        await msg.channel.send("No update script found")

@client.command("addfile")
async def addfile(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return
    message = msg.message
    if len(message.attachments) != 1:
        await msg.send("Please attach a single file to this message")
        return
    f = Path(message.attachments[0].filename)
    if f.is_file() and "-o" not in args and "-a" not in args:
        await msg.send("File already exists. Please specify either -o to overwrite or -a to add a duplicate")
        return
    if len(args) > 1:
        await msg.send("Please specify a single argument -o to overwrite or -a to add a duplicate")
        return
    if len(args) == 1:
        if args[0] == "-o":
            os.remove(message.attachments[0].filename)
        if args[0] == "-a":
            filename = findNewFilename(message.attachments[0].filename)
            await message.attachments[0].save(filename, seek_begin=True, use_cached=False)
            await msg.send('File added with filename "' + filename + '".')
            return     
    await message.attachments[0].save(message.attachments[0].filename, seek_begin=True, use_cached=False)
    await msg.send('File added with filename "' + message.attachments[0].filename + '".')

@client.command("remfile")
async def remfile(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return
    if len(args) != 1:
        await msg.send("Filename not specified")
    
    f = Path(args[0])
    if not f.is_file() or "/" in args[0] or "\\" in args[0] or args[0] in sourceFiles:
        await msg.send("File does not exist")
        return
    os.remove(args[0])
    await msg.send('File removed')

@client.command("listfiles")
async def listfiles(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return
    message = ""
    for file in os.listdir('./'):
        if file not in sourceFiles:
            message += file + "\n"
    if message == "":
        message = "None"
    await msg.send("Files currently saved are as follows\n\n" + message)

@client.command("lock")
async def lock(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return

    # Find the role that affects send message permissions in this channel
    roleName = msg.channel.name.upper()
    guild = msg.guild
    role = None
    for i in guild.roles:
        if i.name == roleName:
            role = i

    # The role name needs to match the uppercase version of the channel name. This will be the case if channels have been made with the automatic channel creation
    if role == None:
        await msg.channel.send("Channel can not be locked")
        return

    # Lock the channel
    lockedChannels.append(msg.channel.name)
    await msg.message.delete(delay=None)
    await msg.channel.set_permissions(role, read_messages=True, send_messages=False)
    data = {'channels':lockedChannels}

    # Set up a way to unlock the channel
    channel = await msg.channel.send("Channel locked! React with trusted permissions to unlock!")
    await channel.add_reaction("🔓") 

    # Save the list of currently locked channels incase the bot goes offline
    f = open("locked.dat", "w")
    json.dump(data, f)
    f.close()

try:
    client.run(OAuthToken)
    print('Closed')
except:
    print("Error starting bot, check OAuth token in Config")
