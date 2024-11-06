import collections
from config.variables import constants
from datetime import datetime, timedelta
from disnake import AllowedMentions, ApplicationCommandInteraction, Guild, Message, Reaction, TextChannel
from disnake.abc import GuildChannel
from disnake.ext import commands, tasks
from services.aws.dynamodb import DynamodbExtractor, DynamodbItem
from tools.archivist.logger import Logger
from tools.directory_managers import create_directory
from tools.message_splitter import MessageSplitter
from tools.text_managers import read_yaml, write_yaml
import os


class GameHandler(DynamodbItem):
    def __init__(self, channel_id: str, game_id: int, last_message_id: int = 0):
        super().__init__(f"test_{channel_id}", game_id)
        self.__last_message_id: int = last_message_id
        self._item = {
            "item_type": self._item["item_type"],
            "item_id": self._item["item_id"]
        }

    def add_info(self, info: dict) -> None:
        self._item["info"] = info
        return

    def add_message(self, message_type, message: Message) -> None:
        message_info = {
            "message_id": message.id,
            "content": message.content,
            "attachments": [x.url for x in message.attachments],
            "date": str(message.created_at),
            "author_id": message.author.id
        }
        self._item["date_end"] = str(message.created_at)
        self.__last_message_id = message.id
        if message_type in ["new_game", "good_answer"]:
            self._item[message_type] = message_info
        elif message_type not in self._item.keys():
            self._item[message_type] = []
            self._item[message_type].append(message_info)
        else:
            self._item[message_type].append(message_info)
        return

    def get_last_message_id(self):
        return self.__last_message_id

    def save(self) -> None:
        self._update_item()
        return


class TestCollector(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.__bot: commands.InteractionBot = bot
        self.__guild: Guild = self.__bot.guilds[0]
        self.__settings_directory: str = constants.DIRECTORY_TEST_COLLECTOR
        create_directory(self.__settings_directory)
        self.__settings: dict = {}
        self.__read_settings()
        self.__settings_default()
        self.__collect_tests.start()
        self.__game: GameHandler = None
        self.__first_game_of_channel_collection: bool = True
        self.__channel_games_collected: int = -1
        self.__ranking_period_options: list[str] = ["un jour", "une semaine", "un mois", "un an", "tout le temps"]

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
        return

    def __check_settings_existence(self, name: str) -> dict:
        if name not in self.__settings.keys():
            self.__settings[name] = {}
        return self.__settings[name]

    @commands.slash_command()
    @commands.default_member_permissions(moderate_members=True)
    async def test(self, interaction: ApplicationCommandInteraction) -> None:
        return

    @test.sub_command_group()
    async def settings(self, interaction: ApplicationCommandInteraction) -> None:
        return

    @settings.sub_command()
    async def create(self, interaction: ApplicationCommandInteraction, channel: GuildChannel, type: str,
                     new_game: str = "🔴", clue: str = "🟠", good_answer: str = "🟢", close: str = "🤏",
                     wrong_answer: str = ":poucebasrouge: 👎", yes: str = "👍 :poucehautvert: :correct: :correct_anim:",
                     no: str = ":Faux: :Faux_anim:", start: bool = False) -> None:
        """
        Crée les paramètres de collecte d'un test.

        Parameters
        ----------
        channel: class: GuildChannel
            Le salon ou fil concerné.
        type: class: str
            Le type de test dont il s'agit.
        new_game: class: str
            Emojis signalant un nouveau jeu. Par défaut : 🔴
        clue: class: str
            Emojis signalant un indice. Par défaut : 🟠
        good_answer: class: str
            Emojis signalant une bonne réponse. Par défaut : 🟢
        close: class: str
            Emojis signalant une réponse approchante. Par défaut : 🤏
        wrong_answer: class: str
            Emojis signalant une mauvaise réponse. Par défaut : :poucebasrouge: 👎
        yes: class: str
            Emojis pour répondre oui à une question. Par défaut : 👍 :poucehautvert: :correct: :correct_anim:
        no: class: str
            Emojis pour répondre non à une question. Par défaut : :Faux: :Faux_anim:
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.create',
            message_start=f"""{interaction.author.mention} a demandé la création des paramètres de collecte de {channel.mention}.""",
            message_success=f"""Les paramètres de collecte de {channel.mention} ont été créés.""",
            message_failure=f"""Les paramètres de collecte de {channel.mention} n'ont pas été créés.""",
            interaction=interaction
        )

        await logger.log_start()

        channel_id: str = str(channel.id)
        settings: dict = self.__check_settings_existence(channel_id)

        if settings:
            await logger.log_message(f"Des paramètres de collecte existent déjà pour {channel.mention}")
            return await logger.log_failure()

        settings["info"] = {
            "name": channel.name,
            "url": channel.jump_url,
            "type": type
        }
        settings["emoji"] = {
            "new_game": new_game,
            "clue": clue,
            "good_answer": good_answer,
            "close": close,
            "wrong_answer": wrong_answer,
            "yes": yes,
            "no": no
        }
        settings["collection"] = {
            "active": start,
            "last_game_id": 0,
            "last_message_id": 0
        }

        self.__write_settings(channel_id)
        return await logger.log_success()

    @settings.sub_command()
    async def edit(self, interaction: ApplicationCommandInteraction, channel: GuildChannel, type: str = None,
                   new_game: str = None, clue: str = None, good_answer: str = None, close: str = None,
                   wrong_answer: str = None, yes: str = None, no: str = None) -> None:
        """
        Modifie les paramètres de collecte d'un test.

        Parameters
        ----------
        channel: class: GuildChannel
            Le salon ou fil concerné.
        new_game: class: str
            Emojis signalant un nouveau jeu.
        clue: class: str
            Emojis signalant un indice.
        good_answer: class: str
            Emojis signalant une bonne réponse.
        close: class: str
            Emojis signalant une réponse approchante.
        wrong_answer: class: str
            Emojis signalant une mauvaise réponse.
        yes: class: str
            Emojis pour répondre oui à une question.
        no: class: str
            Emojis pour répondre non à une question.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.edit',
            message_start=f"""{interaction.author.mention} a demandé la modification des paramètres de collecte de {channel.mention}.""",
            message_success=f"""Les paramètres de collecte de {channel.mention} ont été modifiés.""",
            message_failure=f"""Les paramètres de collecte de {channel.mention} n'ont pas été modifiés.""",
            interaction=interaction
        )

        await logger.log_start()

        channel_id: str = str(channel.id)
        settings: dict = self.__check_settings_existence(channel_id)

        if not settings:
            await logger.log_message(f"{channel.mention} n'a pas de paramètres de collecte.")
            return await logger.log_failure()

        settings["info"]["type"] = type if type else settings["info"]["type"]
        settings["emoji"] = {
            "new_game": new_game if new_game else settings["emoji"]["new_game"],
            "clue": clue if clue else settings["emoji"]["clue"],
            "good_answer": good_answer if good_answer else settings["emoji"]["good_answer"],
            "close": close if close else settings["emoji"]["close"],
            "wrong_answer": wrong_answer if wrong_answer else settings["emoji"]["wrong_answer"],
            "yes": yes if yes else settings["emoji"]["yes"],
            "no": no if no else settings["emoji"]["no"]
        }
        self.__write_settings(channel_id)
        return await logger.log_success()

    @settings.sub_command()
    async def delete(self, interaction: ApplicationCommandInteraction, channel: GuildChannel,
                     confirmation: str = None) -> None:
        """
        ⚠️⚠️⚠️️ ACTION IRRÉVERSIBLE ⚠️⚠️⚠️. Supprime les paramètres de collecte d'un fil ou salon.

        Parameters
        ----------
        channel: class: str
            Le fil ou salon dont on veut supprimer les paramètres.
        confirmation: class: str
            Pour valider la suppression, taper "SUPPRIMER LE TEST"
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.delete',
            message_start=f"""{interaction.author.mention} a demandé la suppression des paramètres de collecte de {channel.mention}.""",
            message_success=f"""Les paramètres de collecte de {channel.mention} ont été supprimés.""",
            message_failure=f"""Les paramètres de collecte de {channel.mention} n'ont pas été supprimés.""",
            interaction=interaction
        )

        await logger.log_start()

        if not confirmation == "SUPPRIMER LE TEST":
            await logger.log_message(
                f"""La confirmation de la suppression des paramètres de collecte de {channel.mention} n'a pas été correctement saisie.""")
            return await logger.log_failure()

        channel_id = str(channel.id)
        settings = self.__check_settings_existence(channel_id)

        if not settings:
            await logger.log_message(f"{channel.mention} n'a pas de paramètres de collecte.")
            return await logger.log_failure()

        self.__settings[channel_id] = {}

        file_name = channel_id + '.yml'
        file_path = self.__settings_directory + file_name
        try:
            os.remove(file_path)
        except:
            await logger.log_message(f"""Les paramètres de collecte de {channel.mention} n'ont pas été trouvés.""")
            return await logger.log_failure()

        return await logger.log_success()

    @test.sub_command_group()
    async def collection(self, interaction: ApplicationCommandInteraction) -> None:
        return

    @collection.sub_command()
    async def start(self, interaction: ApplicationCommandInteraction, channel: GuildChannel) -> None:
        """
        Active la collecte d'un test.

        Parameters
        ----------
        channel: class: GuildChannel
            Le salon ou fil concerné.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.start',
            message_start=f"""{interaction.author.mention} a demandé l'activation de la collecte de {channel.mention}.""",
            message_success=f"""La collecte de {channel.mention} a été activée.""",
            message_failure=f"""La collecte de {channel.mention} n'a pas été activée.""",
            interaction=interaction
        )

        await logger.log_start()

        channel_id: str = str(channel.id)
        settings: dict = self.__check_settings_existence(channel_id)

        if not settings:
            await logger.log_message(f"{channel.mention} n'a pas de paramètres de collecte.")
            return await logger.log_failure()

        settings["collection"]["active"] = True
        self.__write_settings(channel_id)
        return await logger.log_success()

    @collection.sub_command()
    async def pause(self, interaction: ApplicationCommandInteraction, channel: GuildChannel) -> None:
        """
                Désactive la collecte d'un test.

                Parameters
                ----------
                channel: class: GuildChannel
                    Le salon ou fil concerné.
                """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.pause',
            message_start=f"""{interaction.author.mention} a demandé la désactivation de la collecte de {channel.mention}.""",
            message_success=f"""La collecte de {channel.mention} a été désactivée.""",
            message_failure=f"""La collecte de {channel.mention} n'a pas été désactivée.""",
            interaction=interaction
        )

        await logger.log_start()

        channel_id: str = str(channel.id)
        settings: dict = self.__check_settings_existence(channel_id)

        if not settings:
            await logger.log_message(f"{channel.mention} n'a pas de paramètres de collecte.")
            return await logger.log_failure()

        settings["collection"]["active"] = False
        self.__write_settings(channel_id)
        return await logger.log_success()

    @collection.sub_command()
    async def reset(self, interaction: ApplicationCommandInteraction, channel: GuildChannel) -> None:
        """
        Remet la collecte d'un test à zéro.

        Parameters
        ----------
        channel: class: GuildChannel
            Le salon ou fil concerné.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.reset',
            message_start=f"""{interaction.author.mention} a demandé la remise à 0 de la collecte de {channel.mention}.""",
            message_success=f"""La collecte de {channel.mention} a été remise à zéro.""",
            message_failure=f"""La collecte de {channel.mention} n'a pas été remise à zéro.""",
            interaction=interaction
        )

        await logger.log_start()

        channel_id: str = str(channel.id)
        settings: dict = self.__check_settings_existence(channel_id)

        if not settings:
            await logger.log_message(f"{channel.mention} n'a pas de paramètres de collecte.")
            return await logger.log_failure()

        settings["collection"] = {
            "active": settings["collection"]["active"],
            "last_game_id": 0,
            "last_message_id": 0
        }

        self.__write_settings(channel_id)
        return await logger.log_success()

    @collection.sub_command()
    async def check(self, interaction: ApplicationCommandInteraction, channel: GuildChannel) -> None:
        """
        Affiche informations relatives à la collecte d'un test.

        Parameters
        ----------
        channel: class: str
            Le fil ou salon dont on veut afficher les informations.
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.check',
            message_start=f"""{interaction.author.mention} a demandé l'affichage des informations de collecte de {channel.mention}.""",
            interaction=interaction
        )

        await logger.log_start()

        channel_id: str = str(channel.id)
        settings: dict = self.__check_settings_existence(channel_id)

        if not settings:
            await logger.log_message(f"{channel.mention} n'a pas de paramètres de collecte.")
            return await logger.log_failure(
                f"Les informations de collecte de {channel.mention} n'ont pas été affichées.")

        text = f"{channel.mention}"
        text += f"""\n**__Type de test__** : {settings["info"]["type"]}"""
        text += f"""\n**__Jeux récoltés__** : {settings["collection"]["last_game_id"]}"""
        text += "\n**__Emojis utilisés__** :"
        for key, value in settings["emoji"].items():
            text += f"\n\t{key} : {value}"

        message = await interaction.channel.send(text)
        return await logger.log_success(
            f"Les paramètres de collecte de {channel.mention} ont été affichées. {message.jump_url}")

    @test.sub_command()
    async def ranking(self, interaction: ApplicationCommandInteraction, channel: GuildChannel, period: str,
                      top: int = 0) -> None:
        """
        Affiche informations relatives à la collecte d'un test.

        Parameters
        ----------
        channel: class: str
            Le fil ou salon dont on veut afficher les informations.
        period: class: str
            La période de temps à prendre en compte pour le classement
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.test.ranking',
            message_start=f"""{interaction.author.mention} a demandé un top pour le test {channel.mention}.""",
            message_failure=f"""Le top de {channel.mention} n'a pas été affiché.""",
            interaction=interaction
        )

        await logger.log_start()

        channel_id: str = str(channel.id)
        settings: dict = self.__check_settings_existence(channel_id)

        if not settings:
            await logger.log_message(f"{channel.mention} n'a pas de paramètres de collecte.")
            return await logger.log_failure()

        if period not in self.__ranking_period_options:
            await logger.log_message(f"La période indiquée pour le top de {channel.mention} est invalide")
            return await logger.log_failure()

        date_now = datetime.now()
        if period == "un jour":
            date_min = date_now - timedelta(days=1)
        elif period == "une semaine":
            date_min = date_now - timedelta(weeks=1)
        elif period == "un mois":
            date_min = date_now - timedelta(weeks=4)
        elif period == "un an":
            date_min = date_now - timedelta(weeks=52)
        else:
            date_min = datetime.fromisoformat("1970-01-01")

        text = f"""**__Top {top if top > 0 else "complet"}__** : {channel.mention}"""
        text += f"""\n**__Période__** : {period}"""

        item_type = f"test_{channel_id}"
        extraction = DynamodbExtractor(item_type).extraction

        winner_ids = [x["good_answer"]["author_id"] for x in extraction if
                      "good_answer" in x.keys() and x["date_end"] > str(date_min)]
        ranking_raw = collections.Counter(winner_ids).most_common(top if top > 0 else None)
        for winner in ranking_raw:
            try:
                member = await self.__guild.fetch_member(winner[0])
                member = member.mention
            except:
                member = f"<@{winner[0]}>"
            finally:
                pass
            text += f"""\n\t{member} : {winner[1]} point{"s" if winner[1] > 1 else ""}."""

        messages = MessageSplitter(text).get_message_split()
        output: Message = await interaction.channel.send(messages[0],
                                                         allowed_mentions=AllowedMentions(everyone=False, users=False))
        for message in messages[1:]:
            await interaction.channel.send(message)

        return await logger.log_success(f"Le top du test {channel.mention} a été affiché. {output.jump_url}")

    @ranking.autocomplete("period")
    async def autocomplete_ranking_period(self, interaction: ApplicationCommandInteraction, user_input: str):
        string = user_input.lower()
        return [x for x in self.__ranking_period_options if string in x]

    @create.autocomplete("type")
    @edit.autocomplete("type")
    async def autocomplete_test_type(self, interaction: ApplicationCommandInteraction, user_input: str):
        string = user_input.lower()
        options_raw = [x["info"]["type"] for x in self.__settings.values()]
        options = []
        for option in options_raw:
            if option not in options:
                options.append(option)
        return [x for x in options if string in x]

    @tasks.loop(hours=24)
    async def __collect_tests(self) -> None:
        logger = Logger(
            self.__bot,
            log_group='Tâche',
            task_info='task.test.collect'
        )

        await logger.log_start("Début de la collecte des tests.")

        channels_to_collect = {}
        for key, settings in self.__settings.items():
            if settings["collection"]["active"]:
                channels_to_collect[key] = settings

        for channel_id in channels_to_collect.keys():
            try:
                channel: TextChannel = await self.__guild.fetch_channel(channel_id)
                await self.__collect_channel(channel, logger)
            except:
                await logger.log_message(f"""Impossible de collecter sur le fil ou salon "**{self.__settings[channel_id]["info"]["name"]}**" (id : {channel_id}).""")
            finally:
                pass

        self.__read_settings()
        return await logger.log_success("Fin de la collecte des tests.")

    async def __collect_channel(self, channel: TextChannel, logger: Logger) -> None:
        await logger.log_message(f"Collecte de {channel.mention}...")
        channel_id = str(channel.id)
        settings = self.__settings[channel_id]

        last_message_id = settings["collection"]["last_message_id"]
        last_message = await channel.fetch_message(int(last_message_id)) if last_message_id > 0 else None

        self.__create_game(channel_id, settings)
        self.__first_game_of_channel_collection: bool = True
        self.__channel_games_collected: int = -1

        async for message in channel.history(limit=None, after=last_message, oldest_first=True):
            self.__complete_game(channel_id, settings, message)

        self.__write_settings(channel_id)
        self.__channel_games_collected = 0 if self.__channel_games_collected < 0 else self.__channel_games_collected
        await logger.log_message(
            f"Fin de collecte pour {channel.mention}. Tests collectés : {self.__channel_games_collected}.")
        return

    def __create_game(self, channel_id: str, settings: dict) -> None:
        self.__game = GameHandler(
            channel_id=channel_id,
            game_id=settings["collection"]["last_game_id"] + 1,
            last_message_id=settings["collection"]["last_message_id"]
        )
        self.__game.add_info(settings["info"])
        return

    def __complete_game(self, channel_id, settings, message: Message) -> None:
        message_type = self.__check_message_type(settings["emoji"], message)
        if message_type:
            if message_type == "new_game":
                settings["collection"]["last_message_id"] = self.__game.get_last_message_id()
                self.__game.save()
                self.__channel_games_collected += 1
                settings["collection"]["last_game_id"] += 1 if not self.__first_game_of_channel_collection else 0
                self.__first_game_of_channel_collection: bool = False
                self.__create_game(channel_id, settings)
            self.__game.add_message(message_type, message)
        return

    def __check_message_type(self, emoji_settings: dict, message: Message) -> str | None:
        channel_message_types = []
        for reaction in message.reactions:
            channel_message_types.append(self.__check_reaction(emoji_settings, reaction))
        types = ["new_game", "clue", "good_answer", "close", "wrong_answer", "no", "yes"]
        for message_type in types:
            if message_type in channel_message_types:
                return message_type
        return None

    def __check_reaction(self, emoji_settings: dict, reaction: Reaction) -> str | None:
        emoji = self.__get_reaction_text(reaction)
        types = ["new_game", "clue", "good_answer", "close", "wrong_answer", "no", "yes"]
        for message_type in types:
            if emoji in emoji_settings[message_type]:
                return message_type
        return None

    @staticmethod
    def __get_reaction_text(reaction: Reaction) -> str:
        if isinstance(reaction.emoji, str):
            return reaction.emoji
        else:
            return reaction.emoji.name


def setup(bot):
    bot.add_cog(TestCollector(bot))
