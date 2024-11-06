from config.variables import constants
from disnake import AllowedMentions, ApplicationCommandInteraction, Guild, Role, Thread
from disnake.ext.commands import Cog, default_member_permissions, InteractionBot, slash_command
import os
import random
import time
from tools.archivist.logger import Logger
from tools.directory_managers import create_directory
from tools.message_splitter import MessageSplitter
from tools.text_managers import read_yaml, write_yaml


class Moderation(Cog):
    def __init__(self, bot):
        self.__bot: InteractionBot = bot
        self.__guild: Guild = self.__bot.guilds[0]
        self.__settings_directory: str = constants.DIRECTORY_MODERATION
        create_directory(self.__settings_directory)
        self.__settings: dict = {}
        self.__read_settings()
        self.__settings_default()

    def __read_settings(self) -> None:
        for file in self.__get_file_list():
            self.__settings[file[:-4]] = read_yaml(self.__settings_directory + file)

    def __write_settings(self, name: str) -> None:
        file_path = self.__settings_directory + name + '.yml'
        write_yaml(self.__settings[name], file_path)

    def __get_file_list(self) -> list:
        try:
            files = os.listdir(self.__settings_directory)
            return [file for file in files if file[-4:] == '.yml']
        except:
            return []

    def __settings_default(self) -> None:
        watchers = self.__check_settings_existence("watchers")
        if "roles" not in watchers.keys():
            watchers["roles"] = []
        if "watchers" not in watchers.keys():
            watchers["watchers"] = 1
        return

    @slash_command()
    @default_member_permissions(moderate_members=True)
    async def watchers(self, interaction: ApplicationCommandInteraction):
        return

    @watchers.sub_command_group()
    async def role(self, interaction: ApplicationCommandInteraction):
        return

    def __check_settings_existence(self, name: str) -> dict:
        if name not in self.__settings.keys():
            self.__settings[name] = {}
        return self.__settings[name]

    @role.sub_command()
    async def add(self, interaction: ApplicationCommandInteraction, role: Role) -> None:
        """
        Ajouter un role au groupe des observateurs.

        Parameters
        ----------

        role: class: Role
            Le role à ajouter.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.watchers.add',
            message_start=f"""{interaction.author.mention} a demandé l'ajout de {role.mention} au groupe des observateurs.""",
            message_success=f"""Le rôle {role.mention} a été ajouté au groupe des observateurs""",
            message_failure=f"""Le rôle {role.mention} n'a pas été ajouté au groupe des observateurs""",
            interaction=interaction
        )

        await logger.log_start()

        settings = self.__check_settings_existence('watchers')

        if role.id in settings["roles"]:
            await logger.log_message(f"""{role.mention} fait déjà partie du groupe des observateurs.""")
            await logger.log_failure()
            return

        settings["roles"].append(role.id)
        self.__write_settings("watchers")

        await logger.log_success()
        return

    @role.sub_command()
    async def remove(self, interaction: ApplicationCommandInteraction, role: Role) -> None:
        """
        Retirer un role du groupe des observateurs.

        Parameters
        ----------
        role: class: Role
            Le role à retirer.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.watchers.remove',
            message_start=f"""{interaction.author.mention} a demandé le retrait de {role.mention} du groupe des observateurs.""",
            message_success=f"""Le rôle {role.mention} a été retiré du groupe des observateurs""",
            message_failure=f"""Le rôle {role.mention} n'a pas été retiré du groupe des observateurs""",
            interaction=interaction
        )

        await logger.log_start()

        settings = self.__check_settings_existence('watchers')

        if role.id not in settings["roles"]:
            await logger.log_message(f"""{role.mention} ne fait pas partie du groupe des observateurs.""")
            await logger.log_failure()
            return

        settings["roles"].pop(settings["roles"].index(role.id))
        self.__write_settings("watchers")

        await logger.log_success()
        return

    @watchers.sub_command()
    async def check(self, interaction: ApplicationCommandInteraction) -> None:
        """
        Affiche les informations des observateurs.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.watchers.add',
            message_start=f"""{interaction.author.mention} a demandé l'affichage des infos des observateurs.""",
            interaction=interaction
        )

        await logger.log_start()

        settings = self.__check_settings_existence('watchers')

        guild_roles = await self.__guild.fetch_roles()
        watcher_roles = [x for x in guild_roles if x.id in settings["roles"]]

        text = f"""Observateurs par fil : {settings["watchers"]}"""
        text += "\n**__Roles du groupe des observateurs__**" if watcher_roles else "\nAucun rôle dans le groupe des observateurs !"
        for role in watcher_roles:
            text += f"""\n{role.mention}: {" ".join([x.mention for x in role.members])}"""

        messages = MessageSplitter(text).get_message_split()
        mentions = AllowedMentions(everyone=False, users=False, roles=False)
        result = await interaction.channel.send(messages[0], allowed_mentions=mentions)
        for message in messages[1:]:
            await interaction.channel.send(message, allowed_mentions=mentions)

        await logger.log_success(f"""Les infos des observateurs ont été affichées. {result.jump_url}""")
        return

    @watchers.sub_command_group()
    async def number(self, interaction: ApplicationCommandInteraction):
        return

    @number.sub_command()
    async def set(self, interaction: ApplicationCommandInteraction, number: int):
        """
        Définit le nombre d'observateurs par fil de discussion.

        Parameters
        ----------
        number: class: int
            Le nombre d'observateurs. Doit être supérieur à 0.
        """
        settings = self.__check_settings_existence("watchers")

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.watchers.add',
            message_start=f"""{interaction.author.mention} souhaite modifier le nombre d'observateurs par fil.""",
            message_success=f"""Le nombre d'observateurs par fil est réglé sur {number}""",
            message_failure=f"""Le nombre d'observateurs par fil reste de {settings["watchers"]}""",
            interaction=interaction
        )

        await logger.log_start()

        if number < 1:
            await logger.log_message("Le nombre d'observateurs par fil ne peut pas être inférieur à 1.")
            await logger.log_failure()
            return

        if number == settings["watchers"]:
            await logger.log_message(f"Le nombre d'observateurs par fil est déjà de {number}.")
            await logger.log_failure()
            return

        settings["watchers"] = number
        self.__write_settings("watchers")

        await logger.log_success()
        return

    @Cog.listener()
    async def on_thread_create(self, thread: Thread):
        if thread.guild != self.__guild:
            return

        logger = Logger(
            self.__bot,
            log_group='Tâche',
            task_info='task.watchers.add',
            message_failure=f"""Impossible d'ajouter des observateurs à {thread.mention}"""
        )

        settings = self.__check_settings_existence("watchers")
        await logger.log_start(
            f"""Le fil {thread.mention} a été créé par {thread.owner.mention}, il faut {settings["watchers"]} observateur{'s' if settings["watchers"] > 1 else ''}.""")

        guild_roles = await self.__guild.fetch_roles()
        watcher_roles = [x for x in guild_roles if x.id in settings["roles"]]
        if not watcher_roles:
            await logger.log_message(f"""Aucun rôle dans le groupe des observateurs.""")
            await logger.log_failure()
            return

        watcher_users = [x for role in watcher_roles for x in role.members]

        watchers_already_in_thread = [x for x in watcher_users if x == thread.owner]

        watchers_users_unique = []
        for watcher in watcher_users:
            if watcher not in watchers_users_unique and watcher not in watchers_already_in_thread:
                watchers_users_unique.append(watcher)
        watchers_to_add = settings["watchers"] - len(watchers_already_in_thread)

        if watchers_already_in_thread:
            await logger.log_message(
                f"""Observateurs déjà présents sur {thread.mention} : {"".join([x.mention for x in watchers_already_in_thread])}""")
            if watchers_to_add > 0:
                await logger.log_message(
                    f"""Il faut encore ajouter {watchers_to_add} observateur{'s' if watchers_to_add > 1 else ''} au fil {thread.mention}""")

        if watchers_to_add < 1:
            await logger.log_success(
                f"Le nombre requis d'observateurs est déjà sur le fil {thread.mention}. Inutile d'en ajouter.")
            return

        if not watchers_users_unique:
            await logger.log_success(f"Tous les observateurs disponibles sont déjà sur le fil {thread.mention}.")
            return

        if watchers_to_add > len(watchers_users_unique):
            watchers_to_add = len(watchers_users_unique)
            await logger.log_message(
                f"""{watchers_to_add} observateur{'s sont disponibles' if watchers_to_add > 1 else ' est disponible'} pour l'ajout.""")

        random.seed(time.time())
        watchers_picked = random.sample(watchers_users_unique, watchers_to_add)
        for watcher in watchers_picked:
            await thread.add_user(watcher)
            await logger.log_message(f"""{watcher.mention} a été ajouté comme observateur au fil {thread.mention}.""")
        await logger.log_success(
            f"""{watchers_to_add} observateur{'s ont été ajoutés' if watchers_to_add > 1 else ' a été ajouté'} au fil {thread.mention}.""")
        return


def setup(bot):
    bot.add_cog(Moderation(bot))
