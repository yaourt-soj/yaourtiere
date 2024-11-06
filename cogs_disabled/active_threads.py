from config.variables import secrets
from datetime import datetime, timedelta, timezone
from dateutil import tz
from disnake import Guild
from disnake.ext import commands, tasks
from tools.archivist.logger import Logger
from tools.text_managers import read_yaml


class ActiveThreads(commands.Cog):

    def __init__(self, bot):
        self.__bot = bot
        self.__guild: Guild = self.__bot.guilds[0]
        self.__settings = self.__read_settings()
        self.__channel_to_update = self.__bot.get_channel(self.__settings["channel"][secrets.working_environment])
        self.__date = datetime.now(tz=timezone.utc)
        self.__threads = []
        self.__channels_and_threads_dictionaries = []
        self.__instructions = ''
        self.__messages = ['']
        self.refresh_open_threads_list.start()

    @staticmethod
    def __read_settings():
        return read_yaml('config/active_threads.yml')

    def __initialize_run(self) -> None:
        self.__date = datetime.now(tz=timezone.utc)
        self.__settings = self.__read_settings()

    @tasks.loop(hours=1)
    async def refresh_open_threads_list(self) -> None:
        logger = Logger(
            self.__bot,
            log_group='Tâche',
            task_info='task.active threads.update'
        )

        await logger.log_start(f'Mise à jour de {self.__channel_to_update.mention}.')

        self.__initialize_run()
        await self.__collect_channels_and_threads()
        self.__build_message_list()
        await self.__update_active_threads_channel()

        await logger.log_success(f'Mise à jour de {self.__channel_to_update.mention} terminée.')
        return

    async def __collect_channels_and_threads(self) -> None:
        await self.__get_threads_info()
        self.__build_channels_and_threads_list()

    async def __get_threads_info(self) -> None:
        self.__threads = []
        threads_raw = await self.__guild.active_threads()
        for thread in threads_raw:
            thread_dict = {
                "channel": thread.parent,
                "mention": thread.mention,
                "creation_date": thread.created_at,
                "up_date": thread.archive_timestamp,
                "archive_date": await self.__get_thread_archive_date(thread)
            }
            thread_dict["is_dead"] = thread_dict["archive_date"] < datetime.now(tz=timezone.utc)
            self.__threads.append(thread_dict)

    async def __get_thread_archive_date(self, thread) -> datetime:
        up_timestamp = thread.archive_timestamp
        try:
            last_message = await self.__get_thread_last_message_date(thread)
        except:
            last_message = up_timestamp
        last_activity = max(last_message, up_timestamp)
        return last_activity + timedelta(minutes=thread.auto_archive_duration)

    def __build_channels_and_threads_list(self):
        self.__channels_and_threads_dictionaries = []
        while self.__threads:
            channel = self.__threads[0]["channel"]
            threads_channel = [thread for thread in self.__threads if thread["channel"] == channel]
            channel_dictionary = {
                "channel": channel,
                "threads": [thread for thread in threads_channel if not thread["is_dead"]]
            }

            if len(channel_dictionary["threads"]) > 0:
                self.__channels_and_threads_dictionaries.append(channel_dictionary)

            for thread in threads_channel:
                self.__threads.remove(thread)

    @staticmethod
    async def __get_thread_last_message_date(thread) -> datetime:
        message_list = []
        async for item in thread.history(limit=1):
            message_list.append(item)
        last_message = message_list[0]
        return last_message.created_at

    def __build_message_list(self) -> None:
        self.__update_instructions_string()
        self.__messages = [self.__instructions]
        for channel_and_threads in self.__channels_and_threads_dictionaries:
            self.__add_channel_and_threads_to_messages(channel_and_threads)

    def __update_instructions_string(self) -> None:
        self.__instructions = f"""
Au {self.__date.astimezone(tz=tz.gettz('Europe/Paris')).strftime("%d/%m/%Y, %H:%M:%S")} (heure de Paris), voici la liste des fils actifs sur ce serveur Discord.

**__Légende :__**
> :{self.__settings["new"]["emoji"]}: = {self.__settings["new"]["description"]}
> :{self.__settings["up"]["emoji"]}: = {self.__settings["up"]["description"]}
> :{self.__settings["dying"]["emoji"]}: = {self.__settings["dying"]["description"]}
        """

    def __add_channel_and_threads_to_messages(self, channel_and_threads: dict) -> None:
        self.__complete_last_message('\n\n\n')
        self.__complete_last_message(channel_and_threads["channel"].mention)

        for thread in channel_and_threads["threads"]:
            self.__add_thread_to_messages(thread)

    def __complete_last_message(self, string_to_add) -> None:
        last_message_length = len(self.__messages[-1])
        string_to_add_length = len(string_to_add)

        if last_message_length + string_to_add_length <= self.__settings["max_message_length"]:
            self.__messages[-1] += string_to_add
        else:
            self.__messages.append(string_to_add)

    def __add_thread_to_messages(self, thread) -> None:
        thread_string = f"\n> {thread['mention']}"
        thread_string += self.__add_new_emoji_if_required(thread)
        thread_string += self.__add_up_emoji_if_required(thread)
        thread_string += self.__add_dying_emoji_if_required(thread)
        self.__complete_last_message(thread_string)

    def __add_new_emoji_if_required(self, thread) -> str:
        parameters = self.__settings["new"]
        hours_since_creation = (self.__date - thread["creation_date"]).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        return f" :{parameters['emoji']}:" if hours_since_creation < hours_for_emoji else ""

    def __add_up_emoji_if_required(self, thread) -> str:
        parameters = self.__settings["up"]
        thread_is_new = thread["up_date"] + timedelta(minutes=-5) < thread["creation_date"]
        hours_since_up = (self.__date - thread["up_date"]).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        return f" :{parameters['emoji']}:" if hours_since_up < hours_for_emoji and not thread_is_new else ""

    def __add_dying_emoji_if_required(self, thread) -> str:
        parameters = self.__settings["dying"]
        hours_until_archive = (thread["archive_date"] - self.__date).total_seconds() / 3600
        hours_for_emoji = parameters["hours"]
        return f" :{parameters['emoji']}:" if hours_until_archive < hours_for_emoji else ""

    async def __update_active_threads_channel(self) -> None:
        await self.__delete_old_messages()
        await self.__send_new_messages()

    async def __delete_old_messages(self) -> None:
        async for message in self.__channel_to_update.history(limit=None):
            await message.delete()

    async def __send_new_messages(self) -> None:
        for message in self.__messages:
            await self.__channel_to_update.send(message)


def setup(bot):
    bot.add_cog(ActiveThreads(bot))
