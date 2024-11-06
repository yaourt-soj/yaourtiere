import disnake
from datetime import datetime, timezone
from disnake import TextInputStyle, Embed
from disnake.ext import commands
from disnake.ui import Button, View
from services.aws.dynamodb import DynamodbItem
from tools.logger import Logger
from tools.text_managers import read_yaml

top_config = read_yaml('config/golden_silences.yml')


class ActivityTracker(DynamodbItem):
    def __init__(self):
        self.__date = int(datetime.now(timezone.utc).strftime('%Y%m%d'))
        super().__init__(item_type='activity_tracker',
                         item_id=self.__date,
                         get=False)


class GoldenSilencesItem(DynamodbItem):
    def __init__(self, poll: str, user_id: int):
        super().__init__(poll, user_id)

    def get_vote(self, poll_id: str) -> dict:
        output = self._item[poll_id] if poll_id in self._item.keys() else {}
        return output

    def save_vote(self, poll_id: str, vote: list, private_message_id: int, public_message_id: int = None) -> None:
        self._item[poll_id] = self._item[poll_id] if poll_id in self._item.keys() else {}
        self._item[poll_id]["vote"] = vote
        self._item[poll_id]["private_message_id"] = private_message_id

        if public_message_id:
            self._item[poll_id]["public_message_id"] = public_message_id

        self._update_item()


class ModalBuilder(disnake.ui.Modal):
    def __init__(self, bot, poll: dict, poll_range: list, user_id: int):
        self.__bot = bot
        self.__logger = Logger(self.__bot)
        self.__poll_title = poll["title"]
        self.__poll_id = poll["id"]
        self.__poll_range_start = poll_range[0]
        self.__poll_range_end = poll_range[1] + 1
        self.__poll_range = range(self.__poll_range_start, self.__poll_range_end)
        self.__label = poll["vote_label"]
        self.__display_label_rank = poll["vote_rank"]
        self.__placeholder = poll["placeholder"]
        self.__long_input = poll["long_input"]
        self.__max_characters = poll["max_characters"]
        self.__user_id = user_id
        self.__top_item = GoldenSilencesItem(top_config["id"], self.__user_id)
        self.__vote_info = self.__top_item.get_vote(self.__poll_id)
        self.__vote_list = self.__get_vote_list()
        self.__private_message = self.__get_private_message()
        self.__interaction = None

        self.__components = []
        for i in self.__poll_range:
            value = self.__get_vote(i)
            label = self.__label + (' ' + str(i) if self.__display_label_rank else '')
            self.__components.append(disnake.ui.TextInput(
                label=label,
                value=value,
                placeholder=self.__placeholder,
                custom_id=self.__poll_id + '_' + str(i),
                style=TextInputStyle.paragraph if self.__long_input else TextInputStyle.short,
                max_length=self.__max_characters,
                required=False,
            ))
        super().__init__(
            title=self.__poll_title,
            custom_id=f"{self.__poll_id}_{str(poll_range[0])}_{str(poll_range[1])}",
            components=self.__components,
        )

    def __get_vote_list(self):
        output = self.__vote_info["vote"] if "vote" in self.__vote_info.keys() else []
        return output

    def __get_private_message(self):
        output = self.__bot.get_message(
            self.__vote_info["private_message_id"]) if "private_message_id" in self.__vote_info.keys() else None
        return output

    def __get_vote(self, i):
        try:
            vote = self.__vote_info["vote"][i - 1]
        except IndexError:
            vote = ''
        except KeyError:
            vote = ''
        return vote

    async def callback(self, inter: disnake.ModalInteraction):
        self.__interaction = inter
        self.__update_vote_list()
        await self.__interaction.response.defer(with_message=True)
        await self.__send_vote_confirmation()
        self.__push_vote_to_dynamodb()
        await self.__update_poll_buttons()
        await self.__logger.log(
            f"{top_config['title']}: {self.__interaction.user.mention} a voté sur *{self.__poll_title}*")

    def __update_vote_list(self):
        vote_raw = list(self.__interaction.text_values.values())
        vote_clean = [vote.lstrip().rstrip() for vote in vote_raw if vote.lstrip() != ""]
        vote_updated = self.__vote_list.copy()
        vote_updated[self.__poll_range_start - 1: self.__poll_range_end - 1] = vote_clean
        vote_deduplicated = []
        for vote in vote_updated:
            if vote not in vote_deduplicated:
                vote_deduplicated.append(vote)
        self.__vote_list = vote_deduplicated

    async def __send_vote_confirmation(self):
        view = View()
        button = Button(label="Partager mon vote avec la communauté.",
                        style=disnake.ButtonStyle.green,
                        custom_id=f"{top_config['id']}_share_{self.__poll_id}"
                        )
        view.add_item(button)
        embed = Embed(
            title=self.__poll_title,
            description='\n'.join(self.__vote_list)
        )

        if self.__private_message:
            await self.__private_message.delete()
        self.__private_message = await self.__interaction.edit_original_response(content=top_config["thanks"],
                                                                                 embed=embed,
                                                                                 view=view)

    def __push_vote_to_dynamodb(self):
        self.__top_item.save_vote(self.__poll_id, self.__vote_list, self.__private_message.id)

    async def __update_poll_buttons(self):
        view_edit = View()
        buttons = []
        for action_row in self.__interaction.message.components:
            buttons.extend(action_row.children)
        for button in buttons:
            if button.style == disnake.components.ButtonStyle.link:
                button_new = Button(label=button.label,
                                    url=button.url)
            else:
                button_new = Button(label=button.label,
                                    style=disnake.ButtonStyle.green if self.__poll_id == button.custom_id.split('_')[
                                        2] else button.style,
                                    emoji=button.emoji,
                                    custom_id=button.custom_id)
            view_edit.add_item(button_new)
        await self.__interaction.message.edit(view=view_edit)


class PrivateMessage(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__logger = Logger(self.__bot)
        self.__view = None
        self.__current_poll = {}
        self.__current_member = None
        self.__members_contacted = 0
        self.__interaction = None

    @commands.slash_command(default_member_permissions=Permissions(moderate_members=True))
    async def golden_silences_everyone(self, inter):
        f"""
        {top_config['title']}: Demander au bot d'envoyer le MP à tous les membres du serveur.
        """
        await self.__logger.log(
            f"{top_config['title']}: {inter.user.mention} a demandé l'envoi du MP à tous les membres du serveur")
        self.__interaction = inter

        self.__populate_view()
        for member in self.__bot.get_all_members():
            self.__current_member = member
            try:
                await self.__send_vote_options_to_member()
            except:
                pass

        await self.__logger.log(f"{top_config['title']}: Le MP été envoyé à {self.__members_contacted} membre(s).")
        await inter.response.send_message(f"Le MP a été envoyé à {self.__members_contacted} membre(s).")

    def __populate_view(self):
        self.__view = View()
        self.__build_event_link_buttons()
        for poll in top_config["polls"]:
            self.__current_poll = poll
            self.__add_buttons_to_view()

    def __build_event_link_buttons(self):
        links = top_config["links"]
        for key in links.keys():
            button = Button(label=f"{top_config['title']}: {key}",
                            url=links[key]
                            )
            self.__view.add_item(button)

    def __add_buttons_to_view(self):
        if self.__current_poll["options"] <= 5:
            self.__build_and_add_single_button()
        else:
            self.__build_and_add_multiple_buttons()

    def __build_and_add_single_button(self):
        poll_settings = self.__current_poll
        button = Button(label=poll_settings["title"],
                        style=disnake.ButtonStyle.blurple,
                        emoji=poll_settings["emoji"],
                        custom_id=f'{top_config["id"]}_modal_{poll_settings["id"]}_1_{poll_settings["options"]}'
                        )
        self.__view.add_item(button)

    def __build_and_add_multiple_buttons(self):
        poll_settings = self.__current_poll
        poll_options = poll_settings["options"]
        nb_buttons = -(-poll_options // 5)
        for i in range(1, nb_buttons + 1):
            range_start = 5 * (i - 1) + 1
            range_end = 5 * i if i < nb_buttons else poll_options
            button = Button(
                label=f'{poll_settings["title"]} ({range_start} à {range_end})',
                style=disnake.ButtonStyle.blurple,
                emoji=poll_settings["emoji"],
                custom_id=f'{top_config["id"]}_modal_{poll_settings["id"]}_{range_start}_{range_end}'
            )
            self.__view.add_item(button)

    async def __send_vote_options_to_member(self):
        if not self.__current_member.bot:
            self.__members_contacted += 1
            embed = Embed(
                title=top_config["title"],
                description=top_config["welcome"].replace("${user}", self.__current_member.mention),
                colour=0xF0C43F,
                timestamp=datetime.now(timezone.utc)
            )
            await self.__current_member.send(embed=embed, view=self.__view)
            return
        else:
            return

    @commands.slash_command(description=f"{top_config['title']}: Demander au bot de m'envoyer le MP.")
    async def goty(self, inter):
        self.__current_member = inter.user
        self.__populate_view()
        await self.__send_vote_options_to_member()
        await self.__logger.log(f"{top_config['title']}: MP envoyé à {self.__current_member.mention} (commande /goty)")
        await inter.response.send_message(f"{self.__current_member.mention} un message privé t'a été envoyé",
                                          allowed_mentions=disnake.AllowedMentions(everyone=False, users=False),
                                          delete_after=5)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.__track_activity(top_config["id"] + '_PrivateMessage')
        self.__current_member = member
        self.__populate_view()
        await self.__send_vote_options_to_member()
        await self.__logger.log(f"{top_config['title']}: MP envoyé à {self.__current_member.mention} (nouveau membre)")

    @staticmethod
    def __track_activity(detail):
        activity_tracker = ActivityTracker()
        activity_tracker.__increase_counter(f'event.member_join.{detail}')

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        custom_id_split = inter.component.custom_id.split("_")
        if custom_id_split[0] != top_config["id"]:
            return
        elif custom_id_split[1] == 'modal':
            await self.__show_poll_modal(inter, custom_id_split)
        elif custom_id_split[1] == 'share':
            await self.__share_vote_with_community(inter, custom_id_split)
        else:
            await inter.response.send_message("Il n'y a pas d'action définie pour ce bouton")

    async def __show_poll_modal(self, inter, custom_id_split):
        poll_id = custom_id_split[2]
        poll_range = [int(i) for i in custom_id_split[3:]]
        user_id = inter.user.id
        poll = [top for top in top_config["polls"] if top["id"] == poll_id][0]
        await self.__logger.log(f"{top_config['title']}: {inter.user.mention} affiche le formulaire *{poll['title']}*.")
        await inter.response.send_modal(modal=ModalBuilder(self.__bot, poll, poll_range, user_id))

    async def __share_vote_with_community(self, inter, custom_id_split):
        await inter.response.defer(with_message=False)
        poll_id = custom_id_split[2]
        poll_info = [top for top in top_config["polls"] if top["id"] == poll_id][0]
        embed = inter.message.embeds[0]

        top_item = GoldenSilencesItem(top_config["id"], inter.user.id)
        user_vote = top_item.get_vote(poll_id)

        channel_id = poll_info["channel"][config.working_environment]
        channel = self.__bot.get_channel(channel_id)

        if "public_message_id" in user_vote.keys():
            public_message = self.__bot.get_message(user_vote["public_message_id"])
        else:
            public_message = None

        if public_message:
            await public_message.edit(content=f"{inter.author.mention} a voté!", embed=embed,
                                      allowed_mentions=disnake.AllowedMentions(everyone=False, users=False))
        else:
            public_message = await channel.send(content=f"{inter.author.mention} a voté!", embed=embed,
                                                allowed_mentions=disnake.AllowedMentions(everyone=False, users=True))
        public_message_id = public_message.id

        view_private = View()
        button = Button(label="Voir mon vote dans le fil dédié",
                        url=f"https://discord.com/channels/{config.discord_guild}/{channel_id}/{public_message_id}"
                        )
        view_private.add_item(button)
        await inter.message.edit(view=view_private)
        await self.__logger.log(
            f"{top_config['title']}: {inter.user.mention} a publié son vote sur *{poll_info['title']}*")

        top_item.save_vote(poll_id, user_vote["vote"], user_vote["private_message_id"], public_message_id)


def setup(bot):
    bot.add_cog(PrivateMessage(bot))
