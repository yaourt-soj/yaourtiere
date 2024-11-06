import datetime
import disnake
from disnake import TextInputStyle
from disnake.ext import commands


# Subclassing the modal.
class MyModal(disnake.ui.Modal):
    def __init__(self):
        # The details of the modal, and its components
        components = []
        for i in range(1, 6):
            components.append(disnake.ui.TextInput(
                label=f"Jeu #{i}",
                placeholder="Titre",
                custom_id=f"game_{i}",
                style=TextInputStyle.short,
                max_length=200,
            ))
        super().__init__(
            title="Top 10 JV 2022",
            custom_id="create_tag",
            components=components,
        )

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        embed = disnake.Embed(title="Tag Creation")
        for key, value in inter.text_values.items():
            embed.add_field(
                name=key.capitalize(),
                value=value[:1024],
                inline=False,
            )
        await inter.response.send_message(embed=embed)


class PrivateMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def contact_me(self, inter):
        # await inter.response.send_modal(modal=MyModal())

        embed = disnake.Embed(
            title="SoJ d'or 2022",
            description=f"""Bonjour {inter.author.mention}, c'est déjà la fin de l'année, et comme il est de tradition au sein de la communauté "Silence on Joue !", nous organisons des sondages pour récolter l'avis de nos membres concernant la production vidéolusique (mais pas que) de l'année écoulée.""",
            color=disnake.Colour.yellow(),
            timestamp=datetime.datetime.now(),
        )

        await inter.author.send(f"Peek-a-boo {inter.author.mention}!",
                                embed=embed,
                                allowed_mentions=disnake.AllowedMentions(everyone=False, users=False))
        await inter.response.send_message("private message sent")


def setup(bot):
    bot.add_cog(PrivateMessage(bot))
