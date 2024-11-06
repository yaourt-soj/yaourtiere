from disnake import AllowedMentions, Interaction, Message
class Interactor:
    """
    Slash command management
    """

    def __init__(self, interaction: Interaction = None):
        self.__interaction = interaction
        self.__user = self.__interaction.user.mention if interaction else None
        self.__allowed_mentions = AllowedMentions(everyone=False, users=False)
        self.__seconds_before_feedback_deletion = 2

    async def defer(self) -> None:
        """
        Send feedback to user while command is being processed
        """
        if self.__interaction:
            await self.__interaction.response.defer(with_message=True)
        return

    async def reject(self) -> None:
        """
        Send rejection message to user
        """
        await self.__send_feedback(f"⛔️ {self.__user}, tu n'es pas autorisé à utiliser cette commande.")
        return

    async def __send_feedback(self, message) -> None:
        """
        Send a message to the user, then delete it after a while.

        :param message: Message sent to the user
        """
        if self.__interaction:
            await self.__interaction.edit_original_message(message, allowed_mentions=self.__allowed_mentions)
            await self.__interaction.delete_original_message(delay=self.__seconds_before_feedback_deletion)
        return

    async def success(self, log: Message) -> None:
        """
        Send success message to the user
        """
        await self.__send_feedback(f"✅ {self.__user}, ta commande a réussi. Log : {log.jump_url}")
        return

    async def failure(self, log: Message) -> None:
        """
        Send a failure message to the user
        """
        await self.__send_feedback(f"❌ {self.__user}, ta commande a échoué. Log : {log.jump_url}")
        return
