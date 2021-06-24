import discord, json, sys, os
from discord.ext import commands

intents = discord.Intents.all()
client = commands.Bot(command_prefix="$obb", intents=intents)

whitelist = []
logChannelName = ""
with open('config.json') as f:
    data = json.load(f)
    whitelist = data["whitelisted"]
    logChannelName = data["logChannel"]

ignoreMessage = [0]#If a message was deleted as a result of it being a student number, ignore this particular deletion event and don't post it in the log channel

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.name == "student-number-for-verification" and message.author.name not in whitelist:
        channel = discord.utils.get(client.get_all_channels(), guild__name=message.guild.name, name="pending-verifications")
        await channel.send(message.author.mention + " sent in their student number: ```" + message.content + "```")
        ignoreMessage[0] = message.id
        await message.delete(delay=None)

@client.event
async def on_raw_message_delete(rawMessage):
    guild = client.get_guild(rawMessage.guild_id)
    channel = client.get_channel(rawMessage.channel_id)
    if not rawMessage.cached_message or rawMessage.message_id == ignoreMessage[0] or rawMessage.cached_message.author.name in whitelist:
        return    
    message = rawMessage.cached_message
    member = guild.get_member(message.author.id)
    if member == None or member.bot:
        return
    logChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=logChannelName)
    if len(message.attachments) == 0: # There are no attachments, it was just text
        await logChannel.send(message.author.mention + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content)
    else: #There was an attachment
        if message.content != "":
            await logChannel.send(message.author.mention + " deleted a message in " + message.channel.mention + ". The message was: \n\n" + message.content + "\n\nAnd had the following attachment(s)")
        else:
            await logChannel.send(message.author.mention + " deleted a message in " + message.channel.mention + ". The message consisted of the following attachement(s)")
        for i in message.attachments:
            # The cached attachment URL becomes invalid after a few minutes. The following ensures valid media is accessible for moderation purposes
            await i.save(i.filename, seek_begin=True, use_cached=False) # Save the media locally from the cached URL before it becomes invalid
            file = discord.File(fp=i.filename,) # Create a discord file object based on this saved media
            await logChannel.send(content=None,file=file) # Reupload the media to the log channel
            os.remove(i.filename) # Remove the local download of the media
            
@client.event
async def on_raw_message_edit(rawMessage):
    if not rawMessage.cached_message or rawMessage.cached_message.author.name in whitelist:
        return
    guild = client.get_guild(rawMessage.cached_message.author.guild.id)
    channel = client.get_channel(rawMessage.channel_id)
    before = rawMessage.cached_message.content
    try:
        after = rawMessage.data["content"]
    except:
        return
    beforeAttach = rawMessage.cached_message.attachments
    afterAttach = rawMessage.data["attachments"]

    if before == after and len(beforeAttach) == (afterAttach): #Pinning a message triggers an edit event. Ignore it
        return
    
    logChannel = discord.utils.get(client.get_all_channels(), guild__name=guild.name, name=logChannelName)
    if before == "":
        before = "<<No message content>>"
    if after == "":
        after = "<<No message content>>"
        
    await logChannel.send(rawMessage.cached_message.author.mention + " just edited their message in " + channel.mention + ", they changed their original message which said \n\n" + before + "\n\nTo a new message saying \n\n" + after)

    if len(rawMessage.cached_message.attachments) != len(rawMessage.data["attachments"]):
        await logChannel.send("They also changed the attachments as follows. Before: ")
        for i in beforeAttach: # See message delete function for details of the following
            await i.save(i.filename, seek_begin=True, use_cached=False)
            file = discord.File(fp=i.filename,)
            await logChannel.send(content=None,file=file)
            os.remove(i.filename)
        await logChannel.send("After:")
        for i in afterAttach:
            await i.save(i.filename, seek_begin=True, use_cached=False)
            file = discord.File(fp=i.filename,)
            await logChannel.send(content=None,file=file)
            os.remove(i.filename)

client.run('OAuth Goes Here')
print('Closed')
