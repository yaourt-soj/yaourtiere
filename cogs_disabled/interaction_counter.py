import json
from disnake.ext import commands
from tools.logger import Logger
from services.aws.dynamodb import DynamodbItem
from datetime import datetime, timezone


class ActivityTracker(DynamodbItem):
    def __init__(self):
        self.__date = int(datetime.now(timezone.utc).strftime('%Y%m%d'))
        super().__init__(item_type='activity_tracker',
                         item_id=self.__date,
                         get=False)


class InteractionCounter(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__logger = Logger(self.__bot)

    @commands.Cog.listener()
    async def on_interaction(self, inter):
        activity_tracker = ActivityTracker()
        interaction_type = inter.type[0]
        interaction_data = json.loads(json.dumps(inter.data))

        interaction_complement = 'undefined'
        if 'name' in interaction_data.keys():
            interaction_complement = interaction_data['name']
        elif 'custom_id' in interaction_data.keys():
            interaction_complement = interaction_data['custom_id']

        activity_tracker.__increase_counter('interaction.' + interaction_type + '.' + interaction_complement)


def setup(bot):
    bot.add_cog(InteractionCounter(bot))
