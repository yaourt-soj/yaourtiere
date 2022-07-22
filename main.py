from config import config
import datetime
import disnake
from disnake.ui import Button, View
from disnake.ext import commands
from managers import DynamoDBManager
import module

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
    # button_1 = Button(label="Click me!", style=disnake.ButtonStyle.green, emoji="🤴", custom_id="id de mon bouton")
    # button_2 = Button(label="Ignore me!", style=disnake.ButtonStyle.green)
    # view = View()
    # view.add_item(button_1)
    # view.add_item(button_2)
    if message.author == bot.user:
        return
    await module.move_sticky_message(message.channel, bot)
    # await message.channel.send("Coucou !", view=view)


@bot.event
async def on_button_click(inter):
    print('button clicked')
    print(inter.channel.name)
    await inter.response.send_message(inter.component.custom_id)
    print('success')

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return
    if type(reaction.emoji) == str:
        emoji = reaction.emoji
    else:
        emoji = reaction.emoji.name
    if emoji == '🔴':
        await reaction.message.channel.send('Test begins')
    elif emoji == '🟠':
        await reaction.message.channel.send('Test clue')
    elif emoji in ['🟢', 'poucehautvert']:
        await reaction.message.channel.send('Test good answer')
    elif emoji == '🤏':
        await reaction.message.channel.send('Pas loin')
    elif emoji == 'poucebasrouge':
        await reaction.message.channel.send('Mauvaise réponse')
    elif emoji in ['correct_anim', 'correct']:
        await reaction.message.channel.send('Oui à ta question')
    elif emoji in ['Faux_anim', 'Faux']:
        await reaction.message.channel.send('Non à ta question')


@bot.slash_command(description="Considérer ce canal comme un test")
async def channel_is_test(inter, rules_message_id: int = 0):
    message = await inter.channel.send("Making this channel a test")
    dynamo = DynamoDBManager(inter.channel.id)
    dynamo.set_channel_as_test(rules_message_id, message.id)
    await module.move_sticky_message(inter.channel, bot)
    dynamo.push_item_update('channel')
    await inter.response.send_message('Update finished')

@bot.slash_command(description="respons to an idiot")
async def coucou(inter):
    await inter.channel.send("salut <@864750688764559390> !", allowed_mentions=disnake.AllowedMentions(everyone=False, users=False))


@bot.slash_command(description="Testing embeds")
async def embed(inter):
    embed = disnake.Embed(
        title="Embed Title",
        description="Embed Description",
        colour=0xF0C43F,
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url='https://discord.com/channels/342731229315072000/928735760226598933/999734019010859018')
    print(inter.channel)
    await inter.response.send_message('coucou', embed=embed)
    await module.move_sticky_message(inter.channel, bot)


bot.run(TOKEN)



# https://discord.com/api/oauth2/authorize?client_id=999045651893600386&permissions=0&scope=bot%20applications.commands