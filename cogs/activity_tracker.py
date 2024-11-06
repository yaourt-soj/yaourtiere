from datetime import datetime, timezone
from disnake import Guild, Member, Message
from disnake.ext import commands
import math
from services.Amplitude import core as amplitude


class ActivityTracker(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.__bot: commands.InteractionBot = bot
        self.__guild: Guild = self.__bot.guilds[0]

    def __there_is_nothing_to_do(self, message: Message) -> bool:
        if not message.guild:
            return True
        if message.guild != self.__guild:
            return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if self.__there_is_nothing_to_do(message):
            return
        event = {
            "event_type": "Message",
            "user_id": str(message.author.id),
            "device_id": str(message.author.id),
            "time": math.floor(message.created_at.timestamp() * 1000),
            "user_properties": {
                "global_username": message.author.global_name,
                "server_username": message.author.display_name,
                "role": [x.name for x in message.author.roles],
                "top_role": message.author.top_role.name,
                "is_bot": message.author.bot
            },
            "event_properties": {
                "channel_id": str(message.channel.id),
                "channel_name": message.channel.name,
                "parent_id": str(message.channel.parent.id if hasattr(message.channel, 'parent') else message.channel.id),
                "parent_name": message.channel.parent.name if hasattr(message.channel, 'parent') else message.channel.name,
                "message_id": str(message.id),
                "attachments": len(message.attachments)
            }
        }

        tracker = amplitude.AmplitudeManager()
        tracker.track(event)
        return

    # @commands.Cog.listener()
    # async def on_message_edit(self, before: Message, after: Message):
    #     if self.__there_is_nothing_to_do(after):
    #         return
    #     event = {
    #         "event_type": "Message Edit",
    #         "user_id": str(after.author.id),
    #         "device_id": str(after.author.id),
    #         "time": math.floor(datetime.now(tz=timezone.utc).timestamp() * 1000),
    #         "user_properties": {
    #             "username": after.author.display_name,
    #             "role": [x.name for x in after.author.roles],
    #             "top_role": after.author.top_role.name,
    #             "is_bot": after.author.bot
    #         },
    #         "event_properties": {
    #             "channel_id": str(after.channel.id),
    #             "channel_name": after.channel.name,
    #             "parent_id": str(after.channel.parent.id if hasattr(after.channel, 'parent') else after.channel.id),
    #             "parent_name": after.channel.parent.name if hasattr(after.channel, 'parent') else after.channel.name,
    #             "message_id": str(after.id)
    #         }
    #     }
    #     tracker = amplitude.AmplitudeManager()
    #     tracker.track(event)
    #     return

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        event = {
            "event_type": "Member Join",
            "user_id": str(member.id),
            "device_id": str(member.id),
            "time": math.floor(member.joined_at.timestamp() * 1000),
            "user_properties": {
                "username": member.display_name,
                "role": [x.name for x in member.roles],
                "top_role": member.top_role.name,
                "is_bot": member.bot
            }
        }
        tracker = amplitude.AmplitudeManager()
        tracker.track(event)
        return


def setup(bot):
    bot.add_cog(ActivityTracker(bot))
