import aiohttp
import io
import os
import random

from disnake import AllowedMentions, ApplicationCommandInteraction, ChannelType, File, Guild, Message, \
    MessageInteraction, TextChannel, Thread
from disnake.ext import commands
from disnake.ui import Button, View

from config.variables import constants
from services.aws.dynamodb import DynamodbItem
from tools.archivist.logger import Logger
from tools.directory_managers import create_directory
from tools.text_managers import read_yaml, write_yaml


class GameManager(DynamodbItem):
    def __init__(self, channel_id: int | str, game_id: int | str, guild: Guild, thread: Thread):
        super().__init__(f"test_{channel_id}", int(game_id))
        self.__add_missing_elements()
        self.__guild: Guild = guild
        self.__channel_id = channel_id
        self.__game_id = game_id
        self.__thread: Thread = thread
        self.__current_message: dict = {}
        self.__allowed_mentions: AllowedMentions = AllowedMentions(everyone=False, users=False)

    def __add_missing_elements(self):
        for element in ["close", "clue", "wrong_answer", "yes", "no"]:
            if element not in self._item.keys():
                self._item[element] = []

    async def new_game(self) -> Message:
        self.__current_message = self._item["new_game"]
        channel = await self.__get_channel_mention()
        await self.__thread.send(
            f"""__**Jeu n°{self.__game_id} de {channel}, par <@{self.__current_message["author_id"]}>**__""",
            allowed_mentions=self.__allowed_mentions)
        message: Message = await self.__send_message()
        await message.add_reaction("🔴")
        return message

    async def __get_channel_mention(self) -> str:
        mention: str = "**CANAL DISPARU**"
        try:
            channel: Thread = await self.__guild.fetch_channel(self.__channel_id)
            mention: str = channel.mention
        finally:
            return mention

    async def __send_message(self) -> Message:
        message = self.__current_message
        files: list[File] = await AttachmentHandler(message["attachments"]).get_file_list()
        return await self.__thread.send(message["content"], files=files, allowed_mentions=self.__allowed_mentions)

    async def answer(self) -> Message:
        self.__current_message = self._item["good_answer"]
        await self.__thread.send(
            f"""__**La bonne réponse avait été trouvée par <@{self.__current_message["author_id"]}>**__""",
            allowed_mentions=self.__allowed_mentions)
        message: Message = await self.__send_message()
        await message.add_reaction("🟢")
        try:
            await self.__send_link_to_original_channel()
        finally:
            return message

    async def __send_link_to_original_channel(self):
        channel: TextChannel = await self.__guild.fetch_channel(self.__channel_id)
        message: Message = await channel.fetch_message(self._item["new_game"]["message_id"])
        await self.__thread.send(f"""Revoir la discussion d'origine : {message.jump_url}""")

    def get_option_counts(self) -> (int, int, int, int, int):
        clue = len(self._item["clue"])
        close = len(self._item["close"])
        wrong = len(self._item["wrong_answer"])
        yes = len(self._item["yes"])
        no = len(self._item["no"])
        return clue, close, wrong, yes, no

    async def option(self, option_type: str, index: int) -> Message:
        self.__current_message = self._item[option_type][-index - 1]
        if option_type == "close":
            emoji = "🤏"
        elif option_type == "clue":
            emoji = "🟠"
        elif option_type == "wrong_answer":
            emoji = "👎"
        elif option_type == "yes":
            emoji = "✅"
        elif option_type == "no":
            emoji = "❌"
        else:
            emoji = "🤷"
        message: Message = await self.__send_message()
        await message.add_reaction(emoji=emoji)
        return message


class AttachmentHandler:
    def __init__(self, url_list: list[str] = []):
        self.__url_list: list[str] = url_list

    async def get_file_list(self):
        files: list[File] = []
        for url in self.__url_list:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    file = await resp.read()
                    with io.BytesIO(file) as binary:
                        files.append(File(binary, url.split('/')[-1].split('?')[0]))
        return files

    @staticmethod
    async def __get_attachments(attachments: list) -> list[File]:
        files = []
        for attachment in attachments:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment) as resp:
                    file = await resp.read()
                    with io.BytesIO(file) as binary:
                        files.append(File(binary, attachment.split('/')[-1].split('?')[0]))
        return files


class TestReplay(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.__bot: commands.InteractionBot = bot
        self.__guild: Guild = self.__bot.guilds[0]
        self.__settings_directory: str = constants.DIRECTORY_TEST_REPLAY
        self.__test_collector_directory: str = constants.DIRECTORY_TEST_COLLECTOR
        create_directory(self.__settings_directory)
        create_directory(self.__test_collector_directory)
        self.__settings: dict = {}
        self.__collector_info: dict = {}
        self.__read_settings()
        self.__allowed_mentions: AllowedMentions = AllowedMentions(everyone=False, users=False)

    def __read_settings(self) -> None:
        for file in self.__get_file_list(self.__settings_directory):
            self.__settings[file[:-4]] = read_yaml(self.__settings_directory + file)
        for file in self.__get_file_list(self.__test_collector_directory):
            self.__collector_info[file[:-4]] = read_yaml(self.__test_collector_directory + file)

    def __write_settings(self, name: str) -> None:
        file_path = self.__settings_directory + name + '.yml'
        write_yaml(self.__settings[name], file_path)
        self.__read_settings()
        return

    @staticmethod
    def __get_file_list(directory) -> list:
        try:
            files = os.listdir(directory)
            return [file for file in files if file[-4:] == '.yml']
        except:
            return []

    def __settings_default(self) -> None:
        return

    def __check_settings_existence(self, name: str) -> dict:
        settings = self.__settings
        if name not in settings.keys():
            settings[name] = {}
        return settings[name]

    @commands.slash_command()
    async def replay(self, interaction: ApplicationCommandInteraction):
        return

    @replay.sub_command()
    async def infinite(self, interaction: ApplicationCommandInteraction, parent_channel: TextChannel, name: str):
        """
        Crée un replay de test.

        Parameters
        ----------
        parent_channel: class: GuildChannel
            Le salon sur lequel le fil sera créé.
        name: class: str
            Le nom du fil à créer
        """

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='command.replay.infinite',
            message_start=f"""{interaction.author.mention} a demandé la création du replay "**{name}**" sur {parent_channel.mention}.""",
            message_failure=f"""Le replay "**{name}**" n'a pas été créé.""",
            interaction=interaction
        )

        await logger.log_start()

        if hasattr(parent_channel, 'parent'):
            await logger.log_message(f"""{parent_channel.mention} n'est pas un salon.""")
            await logger.log_failure()
            return

        thread = await parent_channel.create_thread(name=name, auto_archive_duration=10080,
                                                    type=ChannelType.public_thread)

        thread_id = str(thread.id)

        settings: dict = self.__check_settings_existence(thread_id)
        self.__pick_question(thread, 'all')

        game = GameManager(settings["test_id"], settings["game_id"], self.__guild, thread)
        message = await game.new_game()

        sticky_view: View = self.__build_new_sticky_view(thread, game, message=message)
        await thread.send(view=sticky_view)

        self.__write_settings(thread_id)
        return await logger.log_success(f"Le replay {message.jump_url} a été créé.")

    def __pick_question(self, thread: Thread, question_type: str) -> None:
        type_settings = []
        for test_settings in self.__collector_info.items():
            if test_settings[1]["info"]["type"] == question_type or question_type == 'all':
                type_settings.extend([test_settings] * test_settings[1]["collection"]["last_game_id"])
        test = random.sample(type_settings, 1)[0]
        test_id = test[0]
        question_range = range(1, test[1]["collection"]["last_game_id"] + 1)
        game_id = random.sample(question_range, 1)[0]

        thread_id = str(thread.id)
        settings: dict = self.__check_settings_existence(thread_id)
        settings["test_id"] = test_id
        settings["game_id"] = game_id
        self.__write_settings(thread_id)

        return

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if self.__there_is_nothing_to_do(message):
            return

        logger = Logger(
            self.__bot,
            log_group='Tâche',
            task_info='task.test.sticky',
            message_success=f"""Sticky rafraîchi dans {message.channel.mention}.""",
        )

        sticky_was_updated = False
        async for msg in message.channel.history(limit=100, before=message):
            if msg.author == self.__bot.user and msg.components:
                view = View()
                for component in msg.components:
                    for button in component.children:
                        view.add_item(Button(
                            label=button.label,
                            emoji=button.emoji,
                            custom_id=button.custom_id,
                            url=button.url
                        ))
                await msg.delete()
                await message.channel.send(view=view)
                sticky_was_updated = True
                break

        if not sticky_was_updated:
            thread: Thread = message.channel
            thread_id: str = str(thread.id)
            settings: dict = self.__check_settings_existence(thread_id)
            game = GameManager(settings["test_id"], settings["game_id"], self.__guild, thread)
            sticky_view: View = self.__build_new_sticky_view(thread, game, message=message)
            await thread.send("Un problème de rafraîchissement des boutons est survenu, ils ont été réinitialisés.")
            await thread.send(view=sticky_view)
            await logger.log_message(f"""Le sticky de {thread.mention} a été reconstruit.""")

        await logger.log_success()

    def __there_is_nothing_to_do(self, message: Message) -> bool:
        if message.author == self.__bot.user:
            return True
        if str(message.channel.id) not in self.__settings.keys():
            return True
        return False

    def __build_new_sticky_view(self, thread: Thread, game: GameManager, options_left: str = None,
                                message: Message = None):
        settings = self.__settings[str(thread.id)]
        settings["question_url"] = message.jump_url if message else settings["question_url"]
        view = View()

        button_question = Button(
            label="Remonter à la question",
            emoji="🔴",
            url=settings["question_url"]
        )
        view.add_item(button_question)

        button_group = "test_replay"
        game_info = f"""{settings["test_id"]}_{settings["game_id"]}"""
        if options_left:
            options_int = []
            for option in options_left.split("_"):
                options_int.append(int(option))
            clue_left, close_left, wrong_left, yes_left, no_left = tuple(options_int)
        else:
            clue_left, close_left, wrong_left, yes_left, no_left = game.get_option_counts()
            options_left = f"{clue_left}_{close_left}_{wrong_left}_{yes_left}_{no_left}"

        if clue_left > 0:
            button_clue = Button(
                label=f"Voir un indice (reste {clue_left})",
                emoji="🟠",
                custom_id=f"""{button_group}|clue|{game_info}|{options_left}"""
            )
            view.add_item(button_clue)
        if yes_left > 0:
            button_yes = Button(
                label=f"Voir une bonne piste (reste {yes_left})",
                emoji="✅",
                custom_id=f"""{button_group}|yes|{game_info}|{options_left}"""
            )
            view.add_item(button_yes)
        if no_left > 0:
            button_no = Button(
                label=f"Voir une fausse piste (reste {no_left})",
                emoji="❌",
                custom_id=f"""{button_group}|no|{game_info}|{options_left}"""
            )
            view.add_item(button_no)
        if wrong_left > 0:
            button_wrong = Button(
                label=f"Voir une mauvaise réponse (reste {wrong_left})",
                emoji="👎",
                custom_id=f"""{button_group}|wrong_answer|{game_info}|{options_left}"""
            )
            view.add_item(button_wrong)
        if close_left > 0:
            button_close = Button(
                label=f"Voir une réponse approchante (reste {close_left})",
                emoji="🤏",
                custom_id=f"""{button_group}|close|{game_info}|{options_left}"""
            )
            view.add_item(button_close)

        button_answer = Button(
            label="Voir la réponse",
            emoji="🟢",
            custom_id=f"""{button_group}|answer|{game_info}"""
        )
        view.add_item(button_answer)

        return view

    @commands.Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        custom_id = interaction.component.custom_id
        if "test_replay" != custom_id[:11]:
            return
        button_type = custom_id.split("|")[1]
        if button_type == "answer":
            await self.__replay_answer(interaction, custom_id, 'all')
        else:
            await self.__replay_option(interaction, custom_id)
        return

    async def __replay_answer(self, interaction: MessageInteraction, button_custom_id: str, question_type: str):
        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='button.replay.answer',
        )
        await logger.log_start(
            f"""{interaction.author.mention} a demandé la réponse dans le replay {interaction.channel.mention}.""")
        await interaction.response.defer()

        thread: Thread = interaction.channel
        custom_id_split = button_custom_id.split('|')
        game_info = custom_id_split[2]
        game_info_split = game_info.split("_")
        test_id = game_info_split[0]
        game_id = game_info_split[1]
        game = GameManager(test_id, game_id, self.__guild, thread)
        await interaction.message.delete()
        await thread.send(f"""||{interaction.author.mention} a demandé à afficher la bonne réponse.||""",
                          allowed_mentions=self.__allowed_mentions)
        message_answer: Message = await game.answer()
        await logger.log_message(f"""La réponse a été affichée. {message_answer.jump_url}""")

        await thread.send("..." + "\n" * 5 + "=" * 40)
        self.__pick_question(thread, question_type)
        thread_id = str(thread.id)
        settings: dict = self.__check_settings_existence(thread_id)
        game = GameManager(settings["test_id"], settings["game_id"], self.__guild, thread)
        message_new = await game.new_game()
        sticky_view: View = self.__build_new_sticky_view(thread, game, message=message_new)
        await thread.send(view=sticky_view)
        return await logger.log_success(f"""Un nouveau jeu a démarré. {message_new.jump_url}""")

    async def __replay_option(self, interaction: MessageInteraction, button_custom_id: str):
        thread: Thread = interaction.channel
        custom_id_split = button_custom_id.split("|")
        option_type = custom_id_split[1]

        logger = Logger(
            self.__bot,
            log_group='Commande',
            task_info='button.replay.' + option_type,
        )
        await logger.log_start(
            f"""{interaction.author.mention} a demandé un complément dans le replay {interaction.channel.mention}.""")
        await interaction.response.defer()

        game_info = custom_id_split[2]
        game_info_split = game_info.split("_")
        test_id = game_info_split[0]
        game_id = game_info_split[1]
        game = GameManager(test_id, game_id, self.__guild, thread)
        options = ["clue", "close", "wrong_answer", "yes", "no"]
        options_left = custom_id_split[3]
        options_left_split = options_left.split("_")
        options_left_split[options.index(option_type)] = str(int(options_left_split[options.index(option_type)]) - 1)
        options_left = "_".join(options_left_split)
        await interaction.message.delete()
        await thread.send(f"""||{interaction.author.mention} a cliqué pour obtenir l'indice suivant :||""",
                          allowed_mentions=self.__allowed_mentions)
        message: Message = await game.option(option_type, int(options_left_split[options.index(option_type)]))
        sticky_view: View = self.__build_new_sticky_view(thread, game, options_left=options_left)
        await thread.send(view=sticky_view)
        return await logger.log_success(f"""Complément affiché. {message.jump_url}""")


def setup(bot):
    bot.add_cog(TestReplay(bot))
