import os
from disnake import Permissions
from disnake.ext import commands
from tools.archivist.logger import Logger


class CogManager(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__this_cog = os.path.basename(__file__).split('.')[0]
        self.__logger = None
        self.__cog_directory = 'cogs'
        self.__cog_list = []
        self.__current_cog = ''
        self.__cogs_unloaded = []
        self.__cogs_loaded = []
        self.__cogs_reloaded = []
        self.__interaction = None
        self.__authorisation_manager = None
        self.__initial_load()

    def __initial_load(self):
        if not list(self.__bot.extensions):
            self.__refresh_cog_list()
            self.__load_all_cogs()

    def __refresh_cog_list(self):
        cog_dir = self.__cog_directory
        self.__cog_list = [x.split('.')[0] for x in os.listdir(cog_dir) if os.path.isfile(f'{cog_dir}/{x}') and x.split('.')[1]=='py']

    def __load_all_cogs(self):
        self.__cogs_loaded = []
        for cog in self.__cog_list:
            self.__current_cog = cog
            self.__load_cog()

    def __load_cog(self):
        if self.__current_cog != self.__this_cog:
            self.__bot.load_extension(self.__cog_directory + '.' + self.__current_cog)
            self.__cogs_loaded.append(self.__current_cog)

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def reload(self, inter):
        return

    @reload.sub_command()
    async def cogs(self, inter):
        """
        Recharge les cogs (sauf le manager).
        """
        self.__logger = Logger(
            self.__bot,
            log_group='Commande ',
            interaction=inter,
            task_info='command.bot.reload cogs'
        )
        await self.__logger.log_start(f'{inter.author.mention} a demandé le rechargement des cogs.')

        self.__unload_all_cogs()
        self.__refresh_cog_list()
        self.__load_all_cogs()
        self.__classify_cogs_unloaded_reloaded_loaded()
        await self.__log_cogs_unloaded_reloaded_loaded()

        await self.__logger.log_success(f'Rechargement des cogs terminé.')

    def __unload_all_cogs(self):
        self.__cogs_unloaded = []
        for extension in list(self.__bot.extensions):
            self.__current_cog = extension.split('.')[-1]
            self.__unload_cog()

    def __unload_cog(self):
        if self.__current_cog != self.__this_cog:
            self.__bot.unload_extension(self.__cog_directory + '.' + self.__current_cog)
            self.__cogs_unloaded.append(self.__current_cog)

    def __classify_cogs_unloaded_reloaded_loaded(self):
        self.__cogs_reloaded = [cog for cog in self.__cogs_unloaded if cog in self.__cogs_loaded]
        self.__cogs_unloaded = [cog for cog in self.__cogs_unloaded if cog not in self.__cogs_reloaded]
        self.__cogs_loaded = [cog for cog in self.__cogs_loaded if cog not in self.__cogs_reloaded]

    async def __log_cogs_unloaded_reloaded_loaded(self):
        message = ''
        if self.__cogs_unloaded:
            message += "\n__Les cogs suivants ont été déchargés__```\n" + "\n".join(self.__cogs_unloaded) + "```"
        if self.__cogs_reloaded:
            message += "\n__Les cogs suivants ont été rechargés__```\n" + "\n".join(self.__cogs_reloaded) + "```"
        if self.__cogs_loaded:
            message += "\n__Les cogs suivants ont été chargés__```\n" + "\n".join(self.__cogs_loaded) + "```"
        if not self.__cogs_loaded and not self.__cogs_reloaded and not self.__cogs_unloaded:
            await self.__logger.log_message("Aucun cog n'a été affecté par l'action")
        else:
            await self.__logger.log_message(message)

    @reload.sub_command()
    async def manager(self, inter):
        """
        Recharge le cog manager.
        """
        self.__logger = Logger(
            self.__bot,
            log_group='Commande ',
            interaction=inter,
            task_info='command.bot.reload cog manager'
        )
        await self.__logger.log_start(f'{inter.author.mention} a demandé le rechargement du cog manager.')

        cog_manager = 'cogs.' + self.__this_cog
        self.__bot.unload_extension(cog_manager)
        self.__bot.load_extension(cog_manager)

        await self.__logger.log_success(f'Rechargement du cog manager terminé.')


def setup(bot):
    bot.add_cog(CogManager(bot))
