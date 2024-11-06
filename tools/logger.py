# Legacy module to drop ASAP

import disnake


class Logger:
    def __init__(self, bot):
        self.__channel = bot.get_channel(config.log_thread)

    async def log(self, message):
        await self.__post(message)

    async def __post(self, message):
        await self.__channel.send(content=message,
                                  allowed_mentions=disnake.AllowedMentions(everyone=False, users=False))

    async def reject(self, interaction):
        await self.__post(f"La demande de {interaction.user.mention} a été rejetée.")
