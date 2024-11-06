from config.variables import secrets
from disnake.ext.commands import InteractionBot
from tools.archivist.logger import Logger
import disnake


class Yaourtiere(InteractionBot):
    def __init__(self):
        self.guild = secrets.discord_guild
        self.__intents = self.__set_intents()
        InteractionBot.__init__(self, test_guilds=[self.guild], intents=self.__intents)
        self.__cog_manager_name = 'cogs.cog_manager'
        self.__token = secrets.discord_bot_token

    @staticmethod
    def __set_intents():
        intents = disnake.Intents.all()
        return intents

    def run_bot(self):
        self.run(self.__token)

    async def on_ready(self):
        logger = Logger(
            self,
            message_start="**========== LE BOT A REDÉMARRÉ ==========**",
            task_info='task.bot.start'
        )
        await logger.log_start(show_emoji=False)
        if self.__cog_manager_name not in self.extensions:
            self.load_extension('cogs.cog_manager')
        message = "__Les cogs suivants ont été chargés au lancement__```\n" + "\n".join(
            [extension.split('.')[-1] for extension in self.extensions]) + "```"
        await logger.log_message(message)


Yaourtiere().run_bot()

