from config.variables import secrets
import boto3


class AwsSessionManager:
    def __init__(self):
        self._session = boto3.Session(
            aws_access_key_id=secrets.aws_access_key_id,
            aws_secret_access_key=secrets.aws_secret_access_key,
            region_name=secrets.aws_region_name
        )
