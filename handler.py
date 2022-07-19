import discord

TOKEN = 'OTM1MTMyNTk1NjUyNTQ2NTkx.G4kysU.MvQN6q9F5xazGN9f7vox7L3QkdaBSQpiyYj65o'

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('Hello bot!'):
        await message.channel.send('Hello World!')

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return

    await reaction.message.channel.send(reaction.emoji)

client.run(TOKEN)