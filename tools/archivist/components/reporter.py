from config.variables import secrets
from disnake import AllowedMentions, Message


class Reporter:
    """
    Reports activity in the bot log thread
    """

    def __init__(self, bot):
        self.__channel = bot.get_channel(secrets.log_thread)

    async def log(self, message) -> Message:
        """
        Forwards a message to the __post method (that will send it to the log thread)

        :param message: Message to be sent to the log thread
        """
        return await self.__post(message)

    async def __post(self, message) -> Message:
        """
        Sends a message to the log thread.

        :param message: Message to be posted.
        """

        return await self.__channel.send(content=message,
                                         allowed_mentions=AllowedMentions(everyone=False, users=False, roles=False),
                                         suppress_embeds=True)

    async def reject(self, user):
        """
        Forwards a rejection message to the __post method (that will send it to the log thread)

        :param user: ID that run the command
        """

        await self.__post(f"La demande de {user} a été rejetée.")
