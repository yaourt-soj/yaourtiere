import boto3
from config import config
from copy import deepcopy

class DynamoDBManager:
    def __init__(self, channel_id):
        self.__table = self.__initiate_table_connection()
        self.__channel_key = {
            "item_type": "channel",
            "item_id": channel_id
        }
        self.channel_item = self.__get_channel_item()

    def __initiate_table_connection(self):
        session = boto3.Session(
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region_name
        )
        return session.resource('dynamodb').Table(config.dynamodb_table)

    def __get_channel_item(self):
        table_object = self.__table.get_item(Key=self.__channel_key)
        output = {"is_test"}
        if 'Item' in table_object.keys():
            output = table_object['Item']
            output.pop('item_type')
            output.pop('item_id')
        return output

    def set_channel_as_test(self, rules_message_id: int, test_start_message_id: int):
        self.channel_item['is_test'] = True
        self.channel_item['test_rules'] = rules_message_id
        if 'test_start_message_id' not in self.channel_item.keys():
            self.channel_item['test_start_message_id'] = test_start_message_id

    def push_item_update(self, item_type: str):
        update_expression_list = []
        update_expression_values = {}

        if item_type == 'channel':
            item = self.channel_item
            item_key = self.__channel_key

        for key in item:
            update_expression_list.extend([f'{key} = :{key}'])
            update_expression_values[f':{key}'] = item[key]

        update_expression = f"SET {', '.join(update_expression_list)}"

        self.__table.update_item(
            Key=item_key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=update_expression_values
        )
