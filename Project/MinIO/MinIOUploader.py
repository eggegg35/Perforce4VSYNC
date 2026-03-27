from minio import Minio
from minio.error import S3Error

import argparse
import os


def ExecutionUpload(file_path):
    # Create MinIO Client.
    Client = Minio('10.8.45.67:9919', access_key='minioadmin', secret_key='minioadmin', secure=False, )

    BucketName = 'engineuse'

    # Validate input file.
    if not os.path.isfile(file_path):
        return 2

    try:
        # Validate bucket availability.
        if not Client.bucket_exists(BucketName):
            return 3

        # Upload single file.
        ObjectName = os.path.basename(file_path)
        Client.fput_object(BucketName, ObjectName, file_path)

        return 0
    except S3Error:
        return 5


if __name__ == '__main__':
    # Parse Command Arguments.
    Parser = argparse.ArgumentParser(description='Upload Files To MinIO')
    Parser.add_argument('--filePath', type=str, required=True, help='Path To Local File')
    Args = Parser.parse_args()

    raise SystemExit(ExecutionUpload(Args.filePath))
