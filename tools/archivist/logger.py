from disnake import Interaction, Message
from tools.archivist.components.interactor import Interactor
from tools.archivist.components.reporter import Reporter
from tools.archivist.components.tracker import Tracker
from tools.message_splitter import MessageSplitter


class Logger:
    def __init__(self, bot, task_info: str, log_group: str = '', message_start: str = '', message_success: str = '',
                 message_failure: str = '', interaction: Interaction = None):
        self.__logger = Reporter(bot)
        self.__interaction = interaction
        self.__interactor = Interactor(self.__interaction)
        self.__tracker = Tracker(self.__interaction, task_info)
        self.__activity_was_tracked = False
        self.__user = interaction.user.mention if interaction else ''
        self.__variables = self.__build_variable_dictionary()
        self.__log_group = log_group
        self.__message_start = self.__replace_variables(message_start)
        self.__message_success = self.__replace_variables(message_success)
        self.__message_failure = self.__replace_variables(message_failure)

    def __build_variable_dictionary(self):
        output = {
            'user': self.__user if self.__user else ''
        }
        return output

    def __replace_variables(self, text):
        for variable in self.__variables:
            text = text.replace(f"${{{variable}}}", self.__variables[variable])
        return text

    async def log_start(self, message: str = None, show_emoji: bool = True):
        self.__track_activity()
        await self.__interactor.defer()
        emoji = self.set_emoji("▶️", show_emoji)
        message = message if message is not None else self.__message_start
        await self.__log(emoji, message)

    @staticmethod
    def set_emoji(emoji: str, show_emoji: bool):
        return emoji if show_emoji else ''

    async def __log(self, emoji: str, message: str) -> Message:
        text = emoji
        text += ' ' + self.__log_group + ' :' if self.__log_group else ''
        text += ' ' + message
        return await self.__logger.log(text)

    def __track_activity(self) -> None:
        if not self.__activity_was_tracked:
            self.__tracker.track_activity()
            self.__activity_was_tracked = True
        return

    async def __log_rejection(self) -> None:
        await self.__interactor.reject()
        await self.__logger.reject(self.__user)
        return

    async def log_message(self, message) -> None:
        message_split = MessageSplitter(message).get_message_split()
        for sub_message in message_split:
            await self.__logger.log(sub_message)
        return

    async def log_success(self, message: str = None, show_emoji: bool = True) -> None:
        self.__track_activity()
        emoji = self.set_emoji("✅", show_emoji)
        message = message if message is not None else self.__message_success
        log_message = await self.__log(emoji, message)
        return await self.__interactor.success(log_message)

    async def log_failure(self, message: str = None, show_emoji: bool = True) -> None:
        self.__track_activity()
        emoji = self.set_emoji("❌", show_emoji)
        message = message if message is not None else self.__message_failure
        log_message = await self.__log(emoji, message)
        return await self.__interactor.failure(log_message)
