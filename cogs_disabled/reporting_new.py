import pandas as pd
from datetime import datetime, timedelta, timezone
from services.aws.dynamodb import DynamodbExtractor as Extractor


class Reporter:
    def __init__(self, bot):
        self.__bot = bot
        self.__extract_days = 365
        self.__today = datetime.now(timezone.utc)
        self.__yesterday = self.__today - timedelta(days=1)
        self.__date_start = self.__yesterday - timedelta(days=self.__extract_days)
        self.__extract_start = int(self.__date_start.strftime('%Y%m%d'))
        self.__extract_end = int(self.__yesterday.strftime('%Y%m%d'))
        self.__extraction = Extractor('activity_tracker', self.__extract_start, self.__extract_end).extraction
        self.__current_item = None
        self.__data_frame = pd.DataFrame()
        self.__populate_data_frame()

    def __populate_data_frame(self):
        for item in self.__extraction:
            self.__current_item = item
            self.__data_frame = pd.concat([self.__data_frame, self.__build_day_data_frame()])
        self.__data_frame['index_split'] = self.__data_frame['index'].apply(lambda x: x.split('.'))
        self.__data_frame['level_one'] = self.__data_frame['index_split'].apply(lambda x: x[0])
        self.__data_frame['level_two'] = self.__data_frame['index_split'].apply(lambda x: x[1])
        self.__data_frame['level_three'] = self.__data_frame['index_split'].apply(lambda x: x[2])
        self.__data_frame.drop(columns=['index', 'index_split'], inplace=True)

    def __build_day_data_frame(self) -> pd.DataFrame:
        del self.__current_item['item_type']
        item_date = datetime.strptime(str(self.__current_item["item_id"]), "%Y%m%d")
        del self.__current_item["item_id"]
        output = pd.DataFrame.from_dict(self.__current_item, orient='index', columns=['count']).reset_index()
        output['date'] = item_date
        return output

    def show_dataframe(self):
        return self.__data_frame



