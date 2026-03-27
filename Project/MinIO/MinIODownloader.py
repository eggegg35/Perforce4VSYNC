from minio import Minio
from minio.error import S3Error

import argparse
import os


def ExecutionDownload(object_name, output_path):
    # Create MinIO Client.
    Client = Minio('10.8.45.67:9919', access_key='minioadmin', secret_key='minioadmin', secure=False, )

    BucketName = 'engineuse'

    if not object_name:
        return 2
    if not output_path:
        return 2

    try:
        # Validate bucket availability.
        if not Client.bucket_exists(BucketName):
            return 3

        AbsOutputPath = os.path.abspath(output_path)
        ParentDir = os.path.dirname(AbsOutputPath)
        Drive, Tail = os.path.splitdrive(ParentDir)
        IsDriveRoot = (Drive != '') and (Tail == '\\' or Tail == '/')

        # Don't try to create drive root like D:\ .
        if ParentDir and (not IsDriveRoot) and (not os.path.isdir(ParentDir)):
            os.makedirs(ParentDir, exist_ok=True)

        Client.fget_object(BucketName, object_name, AbsOutputPath)
        return 0
    except S3Error:
        return 5
    except (OSError, PermissionError) as Ex:
        print('DownloadFileError=' + str(Ex))
        return 6


if __name__ == '__main__':
    # Parse Command Arguments.
    Parser = argparse.ArgumentParser(description='Download File From MinIO')
    Parser.add_argument('--objectName', type=str, required=True, help='Object Name In Bucket')
    Parser.add_argument('--outputPath', type=str, required=True, help='Local Output File Path')
    Args = Parser.parse_args()

    raise SystemExit(ExecutionDownload(Args.objectName, Args.outputPath))
