from minio import Minio
from minio.error import S3Error

import argparse
import json
import os


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "minio_download.json")


def load_download_config(config_path=DEFAULT_CONFIG_PATH):
    if not os.path.isfile(config_path):
        raise FileNotFoundError("Config not found: {0}".format(config_path))

    with open(config_path, "r", encoding="utf-8-sig") as config_file:
        data = json.load(config_file)

    minio_cfg = data.get("minio", {})
    download_cfg = data.get("download", {})

    required_fields = ("endpoint", "access_key", "secret_key", "bucket_name")
    missing = [field for field in required_fields if not str(minio_cfg.get(field, "")).strip()]
    if missing:
        raise ValueError("Missing MinIO fields: {0}".format(", ".join(missing)))

    default_output_dir = str(download_cfg.get("default_output_dir", "")).strip()
    if not default_output_dir:
        raise ValueError("download.default_output_dir is required")

    return {
        "endpoint": minio_cfg["endpoint"],
        "access_key": minio_cfg["access_key"],
        "secret_key": minio_cfg["secret_key"],
        "secure": bool(minio_cfg.get("secure", False)),
        "bucket_name": minio_cfg["bucket_name"],
        "default_output_dir": default_output_dir,
    }


def build_minio_client(config):
    return Minio(
        config["endpoint"],
        access_key=config["access_key"],
        secret_key=config["secret_key"],
        secure=config["secure"],
    )


def resolve_local_output_path(object_name, output_path, default_output_dir):
    object_file_name = os.path.basename(object_name.rstrip("/\\"))
    if not object_file_name:
        raise ValueError("Invalid object_name")

    raw_output = str(output_path or "").strip()
    if not raw_output:
        raw_output = default_output_dir

    abs_output = os.path.abspath(raw_output)
    is_dir_hint = (
        raw_output.endswith(("/", "\\"))
        or os.path.isdir(abs_output)
        or os.path.splitext(abs_output)[1] == ""
    )

    if is_dir_hint:
        return os.path.join(abs_output, object_file_name)
    return abs_output


def ensure_parent_dir(file_path):
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    if parent_dir and (not os.path.isdir(parent_dir)):
        os.makedirs(parent_dir, exist_ok=True)


def ExecutionDownload(object_name, output_path):
    return ExecutionDownloadWithConfig(object_name, output_path, DEFAULT_CONFIG_PATH)


def ExecutionDownloadWithConfig(object_name, output_path=None, config_path=DEFAULT_CONFIG_PATH):
    if not str(object_name or "").strip():
        print("ArgumentError: object_name is required")
        return 2

    try:
        config = load_download_config(config_path)
        client = build_minio_client(config)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print("ConfigError: {0}".format(error))
        return 7

    bucket_name = config["bucket_name"]

    try:
        if not client.bucket_exists(bucket_name):
            print("BucketNotFound: {0}".format(bucket_name))
            return 3

        local_output_path = resolve_local_output_path(
            object_name=object_name,
            output_path=output_path,
            default_output_dir=config["default_output_dir"],
        )
        ensure_parent_dir(local_output_path)

        client.fget_object(bucket_name, object_name, local_output_path)
        print("DownloadSuccess: {0}".format(local_output_path))
        return 0
    except S3Error as error:
        print("MinIOError: {0}".format(error))
        return 5
    except (OSError, PermissionError, ValueError) as error:
        print("FileSystemError: {0}".format(error))
        return 6


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download MinIO object with JSON config")
    parser.add_argument("--objectName", type=str, required=True, help="Object name in bucket")
    parser.add_argument(
        "--outputPath",
        type=str,
        default="",
        help="Output folder or full file path; empty uses download.default_output_dir",
    )
    parser.add_argument(
        "--configPath",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Config file path; default is Project/config/minio_download.json",
    )
    args = parser.parse_args()

    raise SystemExit(
        ExecutionDownloadWithConfig(
            object_name=args.objectName,
            output_path=args.outputPath,
            config_path=args.configPath,
        )
    )
