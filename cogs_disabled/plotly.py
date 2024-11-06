from disnake import Embed, Permissions, ApplicationCommandInteraction, Message
from disnake import Guild, TextChannel
from disnake.ext import commands
from disnake.ui import Button, View
from tools.message_splitter import MessageSplitter
from tools.archivist.logger import Logger
import plotly.express as px
from tools.directory_managers import create_directory


class TestClass(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__guild: Guild = self.__bot.guilds[0]

    @commands.slash_command()
    async def test_plot(self, interaction: ApplicationCommandInteraction):
        logger = Logger(bot=self.__bot,
                        interaction=interaction,
                        task_info='command.test.plot')
        await logger.log_start("début")
        create_directory('temp')
        fig = px.scatter(x=range(10), y=range(10))
        fig.write_html("temp/file.html")

        await logger.log_success("fin")
        return


def setup(bot):
    bot.add_cog(TestClass(bot))
