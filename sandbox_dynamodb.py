import boto3
from config import config

table_name = config.dynamodb_table
channel_id = 935625593167441920

session = boto3.Session(
    aws_access_key_id=config.aws_access_key_id,
    aws_secret_access_key=config.aws_secret_access_key,
    region_name=config.aws_region_name
)

dynamo_table = session.resource('dynamodb').Table(table_name)
item = dynamo_table.get_item(
    Key={
        'item_type': 'channel',
        'item_id': channel_id
    }
)["Item"]

# DELETE ONE ITEM
dynamo_table.delete_item(
    Key={
        'chat_platform': 'Telegram',
        'chat_id': chat_id
    }
)

# DELETE ALL ITEMS
scan = dynamo_table.scan()
with dynamo_table.batch_writer() as batch:
    for each in scan['Items']:
        batch.delete_item(
            Key={
                'chat_platform': each['chat_platform'],
                'chat_id': each['chat_id']
            }
        )


dynamo_table.get_item(
    Key = {
        'id': 1,
        'email': 'fedjioraymond@gmail.com'
    }
)




## All items
dynamo_table = boto3.resource('dynamodb').Table('cs-chat-tickets-dev-bwar')
scan = dynamo_table.scan()
items = scan['Items']


## Create an item
dynamo_table.put_item(Item=mel_item)