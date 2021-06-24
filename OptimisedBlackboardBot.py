import discord

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.channel.name == "student-number-for-verification" and message.author.name != "Bruce the Shark":
        await client.get_channel(811473980329689098).send(message.author.mention + " sent in their student number: ```" + message.content + "```")
        await message.delete(delay=None)

client.run('OAuth Goes Here')
print('Closed')
