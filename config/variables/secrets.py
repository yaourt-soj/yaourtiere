from dotenv import load_dotenv
import os

load_dotenv()

working_environment = os.environ['soj_working_environment']

discord_bot_token = os.environ['soj_discord_bot_token']
discord_guild = int(os.environ['soj_discord_guild'])
log_thread = int(os.environ['soj_log_thread'])
reporting_thread = int(os.environ['soj_reporting_thread'])

aws_access_key_id = os.environ['soj_aws_access_key_id']
aws_secret_access_key = os.environ['soj_aws_secret_access_key']
aws_region_name = os.environ['soj_aws_region_name']

dynamodb_table = os.environ['soj_dynamodb_table']
s3_bucket = os.environ['soj_s3_bucket']

amplitude_api_key = os.environ['soj_amplitude_api_key']