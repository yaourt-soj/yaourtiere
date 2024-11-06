from disnake import AllowedMentions, Guild
from disnake.ext import commands
from random import randrange
from tools.archivist.logger import Logger
from tools.message_splitter import MessageSplitter


class ServerTools(commands.Cog):
    def __init__(self, bot):
        self.__bot: commands.InteractionBot = bot
        self.__guild: Guild = self.__bot.guilds[0]

    @commands.slash_command()
    async def count(self, inter):
        pass

    @count.sub_command()
    async def members(self, inter):
        """
        Compte les membres inscrits sur le serveur.
        """
        logger = Logger(
            self.__bot,
            log_group='Commande',
            message_start=f"""{inter.author.mention} compte les membres du serveur sur {inter.channel.mention}.""",
            message_success=f"""Le compte des membres est fini.""",
            message_failure=f"""Le compte des membres a échoué""",
            task_info='command.server.count_members',
            interaction=inter
        )
        await logger.log_start()

        guild = await self.__bot.fetch_guild(self.__guild.id)

        bot_count: int = len([x for x in self.__guild.members if x.bot])
        bot_string: str = 'bot' + ('s' if bot_count > 1 else '')
        member_count: int = guild.approximate_member_count - bot_count
        member_string: str = 'personne' + ('s' if member_count > 1 else '')
        presence_count: int = guild.approximate_presence_count - bot_count
        presence_string: str = 'personne' + ('s' if presence_count > 1 else '')

        message: str = f"__Membres de **{self.__guild.name}**__"
        message += f"\n👤 {member_count} {member_string}"
        message += f"\n🤖 {bot_count} {bot_string}"
        message += f"\n\n🔌 {presence_count} {presence_string} en ligne"

        await inter.channel.send(message, suppress_embeds=True, allowed_mentions=AllowedMentions(users=False))

        await logger.log_success()
        return


def setup(bot):
    bot.add_cog(ServerTools(bot))
