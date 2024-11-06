from config.variables import secrets
from services.aws.core import AwsSessionManager


class BucketManager(AwsSessionManager):
    def __init__(self):
        AwsSessionManager.__init__(self)
        self._bucket = self._session.resource('s3').Bucket(secrets.s3_bucket)

    def upload(self, file: str, path: str, public: bool = False) -> str:
        extra_args = {}
        if public:
            extra_args['ACL'] = 'public-read'
        self._bucket.upload_file(file, path, ExtraArgs=extra_args)
        return f"https://{secrets.s3_bucket}.s3.amazonaws.com/{path}"
