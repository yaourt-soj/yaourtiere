import disnake
import inspect
from disnake.ext import commands, tasks
from tools.logger import Logger
from services.aws.dynamodb import DynamodbExtractor, DynamodbItem
from datetime import datetime, timedelta, timezone


class ActivityTracker(DynamodbItem):
    def __init__(self):
        self.__date = int(datetime.now(timezone.utc).strftime('%Y%m%d'))
        super().__init__(item_type='activity_tracker',
                         item_id=self.__date,
                         get=False)


class Extractor(DynamodbExtractor):
    def __init__(self, item_type, item_id_min: int = None, item_id_max: int = None):
        DynamodbExtractor.__init__(self,
                                   item_type=item_type,
                                   item_id_min=item_id_min,
                                   item_id_max=item_id_max)


class Reporting(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__channel = self.__bot.get_channel(config.reporting_thread)
        self.__logger = Logger(self.__bot)
        self.__keys_to_ignore = ['item_id', 'item_type']
        self.__yesterday = None
        self.__extract_days = 365
        self.__activity_extract = []
        self.__activity_yesterday = {}
        self.activity.start()

    @tasks.loop(hours=24)
    async def activity(self):
        self.__track_activity()
        await self.__logger.log("Activity reporting: Start")
        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)
        await self.__report_info(f"**========== ACTIVITÉ DU {yesterday.strftime('%Y-%m-%d')} ==========**")
        self.__extract_activity_from_dynamodb()
        await self.__report_activity_for_yesterday()
        await self.__logger.log("Activity reporting: Success")

    @staticmethod
    def __track_activity():
        function_name = inspect.stack()[1][3]
        activity_tracker = ActivityTracker()
        activity_tracker.__increase_counter(f'task.reporting.{function_name}')

    def __extract_activity_from_dynamodb(self):
        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)
        self.__yesterday = int(yesterday.strftime('%Y%m%d'))
        date_start = yesterday - timedelta(days=self.__extract_days)
        extract_start = int(date_start.strftime('%Y%m%d'))
        self.__activity_extract = Extractor('activity_tracker', extract_start, self.__yesterday).extraction

    async def __report_activity_for_yesterday(self):
        activity_yesterday_raw = [item for item in self.__activity_extract if item["item_id"] == self.__yesterday][0]
        self.__activity_yesterday = self.__build_activity_item(activity_yesterday_raw)
        await self.__report_total_activity_yesterday()
        await self.__report_activity_detail_for_yesterday()

    def __build_activity_item(self, raw) -> dict:
        output = {}
        for key, value in raw.items():
            key_split = key.split('.')
            if key not in self.__keys_to_ignore:
                key0 = key_split[0]
                key1 = key_split[1]
                key2 = key_split[2]
                if key0 not in output.keys():
                    output[key0] = {}
                if key1 not in output[key0].keys():
                    output[key0][key1] = {}
                output[key0][key1][key2] = int(value)
        return output

    async def __report_total_activity_yesterday(self):
        total_activity = 0
        for key0 in self.__activity_yesterday.keys():
            for key1 in self.__activity_yesterday[key0].keys():
                total_activity += sum(self.__activity_yesterday[key0][key1].values())
        await self.__report_info(f"**__Nombre d'opérations réalisées:__ {total_activity}**")

    async def __report_info(self, message):
        await self.__channel.send(content=message,
                                  allowed_mentions=disnake.AllowedMentions(everyone=False, users=False))

    async def __report_activity_detail_for_yesterday(self):
        for key0 in self.__activity_yesterday.keys():
            subtotal0 = 0
            for key1 in self.__activity_yesterday[key0].keys():
                subtotal0 += sum(self.__activity_yesterday[key0][key1].values())
            await self.__report_info(f"{' '.join(key0.split('_')).upper()}: {subtotal0}")
            for key1 in self.__activity_yesterday[key0].keys():
                subtotal1 = sum(self.__activity_yesterday[key0][key1].values())
                await self.__report_info(f"> {' '.join(key1.split('_'))}: {subtotal1}")
                for key, value in self.__activity_yesterday[key0][key1].items():
                    await self.__report_info(f"> > _{' '.join(key.split('_'))}:_ {value}")


def setup(bot):
    bot.add_cog(Reporting(bot))
