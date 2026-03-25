import os
import types
import json
import argparse
import sys
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import P4Tool

from clear_folder import clear_folder
from clear_asset import clear_asset
from copy_folder import copy_folder
from copy_asset import copy_asset

BASE_DIR = SCRIPT_DIR
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "branches.json")
DEFAULT_SOURCE_BRANCH = "art"
REQUIRED_BRANCH_FIELDS = ("root", "workspace", "p4_user")

_ACTIVE_CONFIG = None


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    # Accept UTF-8 files both with and without BOM.
    with open(config_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if "branches" not in data:
        raise ValueError("Config file must include 'branches'.")
    return data


def set_active_config(config_path: str = DEFAULT_CONFIG_PATH):
    global _ACTIVE_CONFIG
    _ACTIVE_CONFIG = load_config(config_path)


def get_branch_config(branch_key: str) -> dict:
    if _ACTIVE_CONFIG is None:
        set_active_config(DEFAULT_CONFIG_PATH)
    branches = _ACTIVE_CONFIG.get("branches", {})
    if branch_key not in branches:
        raise ValueError(f"Branch '{branch_key}' not found in config.")
    return branches[branch_key]


def validate_branch_config(branch_key: str):
    branch_cfg = get_branch_config(branch_key)
    for field in REQUIRED_BRANCH_FIELDS:
        value = str(branch_cfg.get(field, "")).strip()
        if not value:
            raise ValueError(
                f"Branch '{branch_key}' config field '{field}' is empty. "
                f"Please update {DEFAULT_CONFIG_PATH}."
            )


def get_branch_path(branch_key: str, user_path: str) -> str:
    return os.path.join(get_branch_config(branch_key)["root"], user_path)


def normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if not normalized:
        return ""
    if not normalized.startswith("unity_project/"):
        normalized = f"unity_project/{normalized}"
    return normalized


def to_windows_path(path: str) -> str:
    return path.replace("/", "\\")


def process_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            paths = []
            for raw_line in file:
                line = normalize_repo_path(raw_line)
                if line:
                    paths.append(line)
            return ", ".join(paths)
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""


def is_unity_folder(path: str) -> bool:
    path = os.path.normpath(path)
    name = os.path.basename(path)
    if os.path.exists(path):
        return os.path.isdir(path)
    return "." not in name


def clear_target_path(path: str):
    if not is_unity_folder(path):
        clear_asset(path)
    else:
        clear_folder(path)


def copy_between_branches(target_path: str, source_branch: str, target_branch: str):
    source_path = get_branch_path(source_branch, target_path)
    target_path_full = get_branch_path(target_branch, target_path)

    clear_target_path(target_path_full)

    if not is_unity_folder(source_path):
        copy_asset(source_path, target_path_full)
    else:
        copy_folder(source_path, target_path_full)


def generate_meta_file_paths(input_list: List[str]) -> List[str]:
    output_list = []
    for file_path in input_list:
        output_list.append(file_path)
        if not file_path.lower().endswith(".meta"):
            output_list.append(f"{file_path}.meta")
    return output_list


def build_sync_targets(full_path: str) -> List[str]:
    normalized = os.path.normpath(full_path)
    targets = [normalized]
    if not normalized.lower().endswith(".meta"):
        targets.append(f"{normalized}.meta")
    return targets


def setup_p4_args(branch_key: str, log_file: str):
    branch_cfg = get_branch_config(branch_key)
    P4Tool.args = types.SimpleNamespace()
    P4Tool.args.p4user = branch_cfg["p4_user"]
    P4Tool.args.p4workspace = branch_cfg["workspace"]
    P4Tool.args.logFile = log_file
    P4Tool.args.retLogFile = log_file
    setattr(P4Tool, "args", P4Tool.args)


def update_multiple_paths(paths: List[str], branch_key: str, log_file: str):
    setup_p4_args(branch_key, log_file)
    for path in paths:
        full_path = get_branch_path(branch_key, path)
        for target in build_sync_targets(full_path):
            P4Tool.p4_update(target)


def build_unlocal_paths(paths: List[str], root_prefix: str) -> List[str]:
    root_prefix = root_prefix.rstrip("\\/")
    normalized_paths = [p.strip().replace("/", os.sep).replace("\\", os.sep) for p in paths if p.strip()]
    return [os.path.join(root_prefix, p) for p in normalized_paths]


def submit_multiple_paths(paths: List[str], branch_key: str, log_file: str, submit_msg: str):
    setup_p4_args(branch_key, log_file)
    path_list = build_unlocal_paths(paths, root_prefix=get_branch_config(branch_key)["root"])
    sub_list = generate_meta_file_paths(path_list)
    P4Tool.p4_commitpathlist(sub_list, commmitMsg=submit_msg)
    print(f"提交路径: {path_list}")


def open_multiple_paths(
    paths: List[str],
    branch_key: str,
    log_file: str,
    open_msg: str,
    pending_message: str = None,
):
    setup_p4_args(branch_key, log_file)
    path_list = build_unlocal_paths(paths, root_prefix=get_branch_config(branch_key)["root"])
    change_id = "New" if pending_message else "default"
    change_msg = pending_message or open_msg
    P4Tool.p4_add_to_changelist(path_list, change_id, change_msg)
    if change_id == "default":
        print(f"已加入默认 pending: {path_list}")
    else:
        print(f"已加入新建 pending: {path_list}")


def apply_operation(paths: List[str], source_branch: str, target_branch: str, operation: str):
    if operation == "delete":
        for path in paths:
            target_path = get_branch_path(target_branch, path)
            clear_target_path(target_path)
        return

    for path in paths:
        copy_between_branches(path, source_branch, target_branch)


def run_branch_sync(
    target_branches: List[str],
    paths: List[str],
    operation: str,
    source_branch: str = DEFAULT_SOURCE_BRANCH,
    submit_message: str = None,
    no_submit: bool = False,
    open_only: bool = False,
    pending_message: str = None,
    dry_run: bool = False,
):
    validate_branch_config(source_branch)
    for target_branch in target_branches:
        validate_branch_config(target_branch)

    if not paths:
        print("错误: 需要至少一个同步文件路径")
        sys.exit(1)

    op = operation.lower()
    if op not in ("add", "modify", "delete"):
        print("错误: operation 仅支持 add / modify / delete")
        sys.exit(1)

    if dry_run:
        print(f"[DRY-RUN] source={source_branch} targets={','.join(target_branches)} operation={op}")
        for p in paths:
            print(f"[DRY-RUN] file: {p}")
        if open_only:
            print("[DRY-RUN] open files to pending (--open-only)")
            if pending_message:
                print(f"[DRY-RUN] pending message: {pending_message}")
        elif no_submit:
            print("[DRY-RUN] skip submit (--no-submit)")
        return

    for target_branch in target_branches:
        if op != "delete":
            update_multiple_paths(paths, source_branch, "p4_update_log.txt")
        update_multiple_paths(paths, target_branch, "p4_update_log.txt")

        apply_operation(paths, source_branch, target_branch, op)

        if open_only:
            default_msg = f"open {op}: {source_branch} -> {target_branch}"
            open_multiple_paths(
                paths,
                target_branch,
                "p4_update_log.txt",
                submit_message or default_msg,
                pending_message=pending_message,
            )
            continue

        if no_submit:
            print(f"已跳过提交（--no-submit）: {source_branch} -> {target_branch}")
            continue

        default_msg = f"sync {op}: {source_branch} -> {target_branch}"
        submit_multiple_paths(paths, target_branch, "p4_update_log.txt", submit_message or default_msg)


def parse_csv_values(raw: str) -> List[str]:
    return [p.strip() for p in raw.split(",") if p.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将 Art 分支内容同步到目标分支")
    parser.add_argument("--branches", required=True, help="目标分支，英文逗号分隔。例如: 001,feature")
    parser.add_argument("--files", required=True, help="需要同步的文件或目录，英文逗号分隔")
    parser.add_argument("--operation", required=True, choices=["add", "modify", "delete"], help="文件操作类型")
    parser.add_argument("--source", default=DEFAULT_SOURCE_BRANCH, help="源分支，默认 art")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="分支配置 JSON 路径")
    parser.add_argument("--message", default=None, help="可选提交说明")
    parser.add_argument("--no-submit", action="store_true", help="只更新+拷贝/删除，不执行提交")
    parser.add_argument("--open-only", action="store_true", help="只打开到默认 pending，不提交")
    parser.add_argument("--pending-message", default=None, help="仅 --open-only 时有效：创建新 pending 并使用该说明")
    parser.add_argument("--dry-run", action="store_true", help="仅打印将要执行的步骤，不实际执行")
    args = parser.parse_args()

    set_active_config(args.config)

    target_branches = parse_csv_values(args.branches)
    raw_paths = parse_csv_values(args.files)
    normalized_paths = [normalize_repo_path(p) for p in raw_paths if normalize_repo_path(p)]

    run_branch_sync(
        target_branches=target_branches,
        paths=normalized_paths,
        operation=args.operation,
        source_branch=args.source,
        submit_message=args.message,
        no_submit=args.no_submit,
        open_only=args.open_only,
        pending_message=args.pending_message,
        dry_run=args.dry_run,
    )
