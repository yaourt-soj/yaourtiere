from config import config
import disnake
from disnake.ext import commands

bot = commands.Bot(
    command_prefix='!',
    test_guilds=[935132340538212413]
)

TOKEN = config.discord_bot_token




@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    message_embed = disnake.Embed(
        title=f'Bienvenue sur {message.channel.name} !',
        description="Ceci est un sticky message pour vous rappeler des choses de base, tout ça tout ça.",
        colour=0xF0C43F,
    )
    print(message_embed)
    async for msg in message.channel.history(limit=20):
        if message_embed in msg.embeds and msg.author == bot.user:
            await msg.delete()
    await message.channel.send(embed=message_embed)


@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    await reaction.message.channel.send(reaction.emoji)

@bot.slash_command(description="respons to an idiot")
async def coucou(inter):
    await inter.response.send_message("salut !")
    async for message in inter.channel.history(limit=100):
        print(message.content)

@bot.slash_command(description="Testing embeds")
async def embed(inter):
    embed = disnake.Embed(
        title="Embed Title",
        description="Embed Description",
        colour=0xF0C43F,
    )
    await inter.response.send_message('coucou', embed=embed)


bot.run(TOKEN)



# https://discord.com/api/oauth2/authorize?client_id=999045651893600386&permissions=0&scope=bot%20applications.commands