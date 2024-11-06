import json
from datetime import datetime, timezone
from services.aws.dynamodb import DynamodbItem


class Tracker(DynamodbItem):
    def __init__(self, interaction=None, task_info: str = ''):
        self.__date = int(datetime.now(timezone.utc).strftime('%Y%m%d'))
        self.__default_value = 'undefined'
        self.__interaction = interaction
        self.__task_info = task_info.split('.') if task_info else []
        self.__counter_name = self.__set_counter_name()
        super().__init__(item_type='activity_tracker',
                         item_id=self.__date,
                         get=False)

    def __set_counter_name(self):
        level_one = self.__get_activity_level_one()
        level_two = self.__get_activity_level_two()
        level_three = self.__get_activity_level_three()
        return '.'.join([level_one, level_two, level_three])

    def __get_activity_level_one(self) -> str:
        output = self.__default_value
        if 0 < len(self.__task_info):
            output = self.__task_info[0]
        elif self.__interaction:
            output = 'interaction'
        return output

    def __get_activity_level_two(self) -> str:
        output = self.__default_value
        if 1 < len(self.__task_info):
            output = self.__task_info[1]
        elif self.__interaction:
            output = self.__interaction.type[0]
        return output

    def __get_activity_level_three(self) -> str:
        output = self.__default_value
        if 2 < len(self.__task_info):
            output = self.__task_info[2]
        elif self.__interaction:
            output = self.__get_interaction_detail()
        return output

    def __get_interaction_detail(self) -> str:
        output = self.__default_value
        data = json.loads(json.dumps(self.__interaction.data))
        if 'name' in data.keys():
            output_pieces = []
            while data:
                output_pieces.append(data["name"])
                data = data["options"][0] if "options" in data.keys() and data["options"] else None
            output = " ".join(output_pieces)
        elif 'custom_id' in data.keys():
            output = data['custom_id']
        return output

    def track_activity(self):
        self.increase_counter(self.__counter_name)
