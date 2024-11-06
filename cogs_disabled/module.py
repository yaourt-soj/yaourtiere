from disnake import channel, Embed, Reaction
from disnake.ext.commands import Bot
from services import DynamoDBManager


async def move_sticky_message(thread: channel, bot: Bot):
    message_embed = Embed(
        title=f'Bienvenue sur {thread.name} !',
        description="""
            L'objectif est de trouver le {type} à partir {source}.
            \nLe maître du jeu actuel est {game_master}.
            \nTu peux poser des questions au MJ auxquelles il peut répondre textuellement, ou avec 🤏 pour oui, 🤏 pour non ou 🤏 pour à peu près.
            \n🤏 indique une mauvaise réponse, 🤏 indique une réponse mauvaise mais proche, 🤏 indique la bonne réponse.
            \nCelui qui trouve la bonne réponse devient le nouvau mâitre du jeu.
            """,
        colour=0xF0C43F,
    )

    async for msg in thread.history(limit=5):
        embed_titles = [i.title for i in msg.embeds]
        if message_embed.title in embed_titles and msg.author == bot.user:
            await msg.delete()
    await thread.send(embed=message_embed)

async def create_new_test(reaction: Reaction):
    dynamo = DynamoDBManager(reaction.message.channel.id)
