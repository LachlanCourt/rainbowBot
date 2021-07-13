import discord, json, sys, os, subprocess
from discord.ext import commands
from pathlib import Path

intents = discord.Intents.all()
client = commands.Bot(command_prefix="$obb", intents=intents)

whitelist = []
trustedRoles = []
logChannelName = ""
reportChannelName = ""
OAuthToken = None
with open('config.json') as f:
    data = json.load(f)
    whitelist = data["whitelisted"]
    trustedRoles = data["trustedRoles"]
    logChannelName = data["logChannel"]
    reportChannelName = data["reportChannel"]
    OAuthToken = data["OAuth"]

try:
    f = open("rolemenu.dat")
    rolemenuData = json.load(f)
    f.close()
except:
    rolemenuData = {}

ignoreMessage = [0]#If a message was deleted as a result of it being a student number, ignore this particular deletion event and don't post it in the log channel

reactions = "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿".split()

sourceFiles = [".git", ".gitignore", "config.json", "OptimisedBlackboardBot.py", "README.md", "Examples", "updatebot.sh"]

permsError = "You don't have permission to use this command"
    
def checkPerms(msg):
    roleNames = []
    for i in range(len(msg.message.author.roles)):
        roleNames.append(msg.message.author.roles[i].name)
    if any(i in roleNames for i in trustedRoles):
        return True
    return False


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.type == discord.ChannelType.private:
        await message.channel.send("Thankyou for your message, it has been passed on to the administrators")
        guilds = message.author.mutual_guilds
        for guild in guilds:
            logChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=logChannelName)
            await logChannel.send(message.author.mention + " sent a DM message, they said\n\n" + message.content)
    if message.channel.type != discord.ChannelType.private and message.channel.name == "student-number-for-verification" and message.author.name not in whitelist:
        channel = discord.utils.get(client.get_all_channels(), guild__name=message.guild.name, name="pending-verifications")
        await channel.send(message.author.mention + " sent in their student number: ```" + message.content + "```")
        ignoreMessage[0] = message.id
        await message.delete(delay=None)
    # Now that the response to any message has been handled, process the official commands
    await client.process_commands(message)

@client.event
async def on_raw_message_delete(rawMessage):
    guild = client.get_guild(rawMessage.guild_id)
    channel = client.get_channel(rawMessage.channel_id)
    if not rawMessage.cached_message or channel.name == "student-number-for-verification" or rawMessage.cached_message.author.name in whitelist:
        return    
    message = rawMessage.cached_message
    member = guild.get_member(message.author.id)
    if member == None or member.bot:
        return
    reportChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=reportChannelName)
    if len(message.attachments) == 0: # There are no attachments, it was just text
        await reportChannel.send(message.author.mention + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content)
    else: #There was an attachment
        if message.content != "":
            await reportChannel.send(message.author.mention + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content + "\n\nAnd had the following attachment(s)")
        else:
            await reportChannel.send(message.author.mention + " deleted a message in " + message.channel.mention + ". The message consisted of the following attachement(s)")
        for i in message.attachments:
            # The cached attachment URL becomes invalid after a few minutes. The following ensures valid media is accessible for moderation purposes
            await i.save(i.filename, seek_begin=True, use_cached=False) # Save the media locally from the cached URL before it becomes invalid
            file = discord.File(fp=i.filename,) # Create a discord file object based on this saved media
            await reportChannel.send(content=None,file=file) # Reupload the media to the log channel
            os.remove(i.filename) # Remove the local download of the media
            
@client.event
async def on_raw_message_edit(rawMessage):
    if not rawMessage.cached_message or rawMessage.cached_message.author.name in whitelist:
        return
    guild = client.get_guild(rawMessage.cached_message.author.guild.id)
    channel = client.get_channel(rawMessage.channel_id)

    member = guild.get_member(rawMessage.cached_message.author.id)
    if member == None or member.bot:
        return
    
    before = rawMessage.cached_message.content
    try:
        after = rawMessage.data["content"]
    except:
        return
    beforeAttach = rawMessage.cached_message.attachments
    afterAttach = rawMessage.data["attachments"]

    if before == after and len(beforeAttach) == len(afterAttach): #Pinning a message triggers an edit event. Ignore it
        return
    
    reportChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=reportChannelName)
    if before == "":
        before = "<<No message content>>"
    if after == "":
        after = "<<No message content>>"
        
    await reportChannel.send(rawMessage.cached_message.author.mention + " just edited their message in " + channel.mention + ", they changed their original message which said \n\n" + before + "\n\nTo a new message saying \n\n" + after)

    if len(rawMessage.cached_message.attachments) != len(rawMessage.data["attachments"]):
        await reportChannel.send("They also changed the attachments as follows. Before: ")
        for i in beforeAttach: # See message delete function for details of the following
            await i.save(i.filename, seek_begin=True, use_cached=False)
            file = discord.File(fp=i.filename,)
            await reportChannel.send(content=None,file=file)
            os.remove(i.filename)
        await reportChannel.send("After:")
        for i in afterAttach:
            await i.save(i.filename, seek_begin=True, use_cached=False)
            file = discord.File(fp=i.filename,)
            await reportChannel.send(content=None,file=file)
            os.remove(i.filename)

@client.event
async def on_raw_reaction_add(reaction):
    if reaction.member.bot: # Ignore reaction remove and add events from itself (when editing the menu)
        return
    # Grab necessary data to analyse the event
    channel = client.get_channel(reaction.channel_id)
    msg = await channel.fetch_message(reaction.message_id)
    roles = await reaction.member.guild.fetch_roles()
    # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they added and give the user that role
    if str(msg.id) in rolemenuData and msg.author == client.user: # The message id comes in as an integer but is serialised as a string when saved to JSON
        roleName = rolemenuData[str(msg.id)][reaction.emoji.name]
        for i in range(len(roles)):
            if roles[i].name == roleName:
                await reaction.member.add_roles(roles[i])

@client.event
async def on_raw_reaction_remove(reaction):
    # Grab necessary data to analyse the event. A lot of the calls used in reaction_add returns null for reaction_remove
    # because they no longer react to the message so bit of a clunky workaround
    guild = client.get_guild(reaction.guild_id)
    member = guild.get_member(reaction.user_id)
    if member.bot: # Ignore reaction remove and add events from itself (when editing the menu)
        return
    roles = await guild.fetch_roles()
    channel = client.get_channel(reaction.channel_id)
    msg = await channel.fetch_message(reaction.message_id)

    # If the message the user reacted to is a rolemenu, get the name of the role related to the reaction they removed and remove that role from the user
    if str(msg.id) in rolemenuData and msg.author == client.user: # The message id comes in as an integer but is serialised as a string when saved to JSON
        roleName = rolemenuData[str(msg.id)][reaction.emoji.name]
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
    try:
        f = open(args[0] + '.json')
        data = json.load(f)
        f.close()
    except:
        await msg.channel.send('Unable to open JSON file "' + args[0] + '" :frowning:')
        return
    statusMessage = await msg.channel.send("File loaded successfully! Creating channels...")

    f = Path("rolemenu.dat")
    createNewMenu = False
    if len(args) > 1 and args[1] == "-c" or not f.is_file():
        createNewMenu = True

    # Check that the target channel exists for the role menu. If not, return and request user run with flag
    if not createNewMenu:
        roleMenuChannel = None
        for i in guild.channels:
            if i.name == data["roleMenuChannel"]:
                roleMenuChannel = i
        if roleMenuChannel == None:
            await statusMessage.edit(content="No channel currently exists for a role menu, but no -c flag was included to create roles clean. Terminating.")
            return

    if f.is_file():
        # Check if we need to remove old rolemenu file
        if createNewMenu: # Will be true if either -c argument was given or if rolemenu.dat does not exist. If it does not exist, removing will throw an exception
            try:
                os.remove("rolemenu.dat")
                global rolemenuData
                rolemenuData = {}
                await statusMessage.edit(content="-c flag included, removing the existing rolemenu.dat...") 
            except:
                pass
        else:
            await statusMessage.edit(content="rolemenu.dat already exists. Appending to existing file...")
    else:
        await statusMessage.edit(content="No rolemenu.dat file found. A new file will be created") 
    
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

    for i in courses:
        await statusMessage.edit(content="Creating " + i + " channels")
        # Create roles and record roles for overwrites
        roleObjs = []
        for j in range(len(courses[i])):
            role = await guild.create_role(name=courses[i][j], colour=255)# Convert HEX code to integer (Bc that makes sense??) this is blue #0000ff
            roleObjs.append(role)
            
        # Create category overwrites and disable to @everyone by default
        categoryOverwrites = {guild.default_role:discord.PermissionOverwrite(view_channel=False)}
        if sinbinRole != None:
            categoryOverwrites[sinbinRole] = discord.PermissionOverwrite(send_messages=False, add_reactions=False, connect=False)
        for j in range(len(roleObjs)):
            categoryOverwrites[roleObjs[j]] = discord.PermissionOverwrite(view_channel=True)
                               
        # Create category and apply overwrites
        category = await guild.create_category(name=i, overwrites=categoryOverwrites)
                               
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
        await guild.create_voice_channel(i, overwrites=categoryOverwrites, category=category)
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
        await statusMessage.edit(content="Creating " + i + " rolemenu")
        # Create message to send
        message = "​\n**" + i + "**\nReact to give yourself a role\n\n"
        currentMenu = {}
        for j in range(len(courses[i])):
            message += reactions[j] + " " + courses[i][j] + "\n\n"
            currentMenu[reactions[j]] = courses[i][j]
            
        menuMessage = await roleMenuChannel.send(message)
        rolemenuData[str(menuMessage.id)] = currentMenu # The message id comes in as an integer, but will be serialised as a string when saved to JSON

        # Add reactions
        for j in range(len(courses[i])):
            await menuMessage.add_reaction(reactions[j])
                                   
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

    if args[1] == "add":
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

    if args[1] == "remove":
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

    if args[1] == "update":
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
    subprocess.call(['sh', './updatebot.sh'])

@client.command("addfile")
async def addfile(msg, *args):
    if not checkPerms(msg): # Check the user has a role in trustedRoles
        await msg.channel.send(permsError)
        return
    message = msg.message
    if len(message.attachments) != 1:
        await msg.send("Please add a single file to this message")
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
            filename = message.attachments[0].filename
            while Path(filename).is_file():
                oldFilename = filename
                filename = ""
                ext = False
                for i in range(len(oldFilename) -1, -1, -1):
                    filename += oldFilename[i]
                    if oldFilename[i] == ".":
                        ext = True
                        filename += ")1(" #Will be reversed
                filename = filename[::-1]
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

try:
    client.run(OAuthToken)
    print('Closed')
except:
    print("Error starting bot, check OAuth in Config")
