import os
import types
import json
import argparse
import sys
import shutil
import stat
import datetime
import urllib.request
import urllib.error
from typing import List, Dict, Any

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
DEFAULT_MSG_API = "http://10.8.45.67:3106/lark_tools_send_msg"
REQUIRED_BRANCH_FIELDS = ("root", "workspace", "p4_user")

_ACTIVE_CONFIG = None


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if "branches" not in data:
        raise ValueError("配置文件必须包含 branches 字段。")
    return data


def set_active_config(config_path: str = DEFAULT_CONFIG_PATH):
    global _ACTIVE_CONFIG
    _ACTIVE_CONFIG = load_config(config_path)


def get_branch_config(branch_key: str) -> dict:
    if _ACTIVE_CONFIG is None:
        set_active_config(DEFAULT_CONFIG_PATH)
    branches = _ACTIVE_CONFIG.get("branches", {})
    if branch_key not in branches:
        raise ValueError(f"配置中不存在分支: {branch_key}")
    return branches[branch_key]


def validate_branch_config(branch_key: str):
    branch_cfg = get_branch_config(branch_key)
    for field in REQUIRED_BRANCH_FIELDS:
        value = str(branch_cfg.get(field, "")).strip()
        if not value:
            raise ValueError(
                f"分支 {branch_key} 的配置项 {field} 为空，请先更新配置文件: {DEFAULT_CONFIG_PATH}"
            )


def get_branch_path(branch_key: str, user_path: str) -> str:
    return os.path.join(get_branch_config(branch_key)["root"], user_path)


def normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if not normalized:
        return ""
    if normalized.lower().endswith(".meta"):
        normalized = normalized[:-5]
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
        print(f"读取列表文件失败: {e}")
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


def remove_single_file(file_path: str):
    if os.path.isfile(file_path):
        try:
            os.chmod(file_path, stat.S_IWRITE)
            os.remove(file_path)
        except Exception as e:
            print(f"删除文件失败: {file_path}, 错误: {e}")


def copy_single_file(src_file: str, dst_file: str):
    if not os.path.isfile(src_file):
        return
    try:
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        if os.path.exists(dst_file):
            os.chmod(dst_file, stat.S_IWRITE)
            os.remove(dst_file)
        shutil.copy2(src_file, dst_file)
    except Exception as e:
        print(f"拷贝文件失败: {src_file} -> {dst_file}, 错误: {e}")


def sync_folder_meta(source_folder: str, target_folder: str):
    source_meta = f"{source_folder}.meta"
    target_meta = f"{target_folder}.meta"
    if not os.path.isfile(source_meta):
        remove_single_file(target_meta)
        return
    copy_single_file(source_meta, target_meta)


def delete_target_path(path: str):
    if not is_unity_folder(path):
        clear_asset(path)
        return

    if os.path.isdir(path):
        def on_rm_error(func, target, exc_info):
            os.chmod(target, stat.S_IWRITE)
            func(target)

        try:
            shutil.rmtree(path, onerror=on_rm_error)
        except Exception as e:
            print(f"删除目录失败: {path}, 错误: {e}")
    remove_single_file(f"{path}.meta")


def copy_between_branches(target_path: str, source_branch: str, target_branch: str):
    source_path = get_branch_path(source_branch, target_path)
    target_path_full = get_branch_path(target_branch, target_path)

    clear_target_path(target_path_full)

    if not is_unity_folder(source_path):
        copy_asset(source_path, target_path_full)
    else:
        copy_folder(source_path, target_path_full)
        sync_folder_meta(source_path, target_path_full)


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
    root_prefix = root_prefix.rstrip("\/")
    normalized_paths = [p.strip().replace("/", os.sep).replace("\\", os.sep) for p in paths if p.strip()]
    return [os.path.join(root_prefix, p) for p in normalized_paths]


def build_change_message(base_msg: str, pending_message: str = None) -> str:
    full_msg = f"p4-bypass p4-admin-bypass {base_msg}"
    trimmed_pending = (pending_message or "").strip()
    if trimmed_pending:
        full_msg = f"{full_msg} {trimmed_pending}"
    return full_msg


def summarize_paths_for_log(paths: List[str], max_chars: int = 140) -> str:
    valid_paths = [p for p in paths if p]
    if not valid_paths:
        return "无文件"

    joined = "，".join(valid_paths)
    if len(joined) <= max_chars:
        return joined

    if len(valid_paths) == 1:
        return valid_paths[0]

    return f"同步了{valid_paths[0]}等{len(valid_paths)}个文件"


def submit_multiple_paths(paths: List[str], branch_key: str, log_file: str, submit_msg: str) -> str:
    setup_p4_args(branch_key, log_file)
    path_list = build_unlocal_paths(paths, root_prefix=get_branch_config(branch_key)["root"])
    sub_list = generate_meta_file_paths(path_list)
    result = P4Tool.p4_commitpathlist(sub_list, commmitMsg=submit_msg)
    print(f"提交路径摘要: {summarize_paths_for_log(path_list)}")
    if result is True:
        print(f"分支 {branch_key} 提交成功。")
        return "成功"
    if result is False:
        print(f"分支 {branch_key} 未提交（可能没有可提交变更）。")
        return "未提交"
    print(f"分支 {branch_key} 提交失败，请查看 p4 日志。")
    return "失败"


def build_email_report(
    records: List[Dict[str, Any]],
    source_branch: str,
    target_branches: List[str],
    operation: str,
    pending_message: str = None,
) -> str:
    lines = [
        "ArtSync 执行报告",
        f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"源分支: {source_branch}",
        f"目标分支: {','.join(target_branches)}",
        f"操作类型: {operation}",
    ]
    if pending_message:
        lines.append(f"追加说明: {pending_message}")
    lines.append("")
    lines.append("执行记录:")

    if not records:
        lines.append("- 无记录")
    else:
        for record in records:
            lines.append(
                f"- 分支={record['branch']} 动作={record['action']} 状态={record['status']} 说明={record['message']}"
            )
            path_summary = summarize_paths_for_log(record.get("paths", []))
            lines.append(f"  文件摘要: {path_summary}")
            lines.append(f"  文件数量: {len(record.get('paths', []))}")
            lines.append("  备注: 已自动处理对应 .meta")

    return "\n".join(lines)


def send_email_report(to_email: str, subject: str, body: str) -> bool:
    msg_api = os.getenv("ARTSYNC_MSG_API", DEFAULT_MSG_API).strip()
    payload = {
        "type": "user",
        "target": to_email,
        "msg": f"{subject}\n\n{body}",
    }
    req = urllib.request.Request(
        msg_api,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            ret = resp.read().decode("utf-8", errors="ignore")
        print(f"消息已发送到邮箱: {to_email}, 返回: {ret}")
        return True
    except urllib.error.HTTPError as e:
        print(f"发送消息失败: HTTP {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"发送消息失败: {e.reason}")
        return False
    except Exception as e:
        print(f"发送消息失败: {e}")
        return False


def open_multiple_paths(
    paths: List[str],
    branch_key: str,
    log_file: str,
    open_msg: str,
    pending_message: str = None,
) -> str:
    setup_p4_args(branch_key, log_file)
    path_list = build_unlocal_paths(paths, root_prefix=get_branch_config(branch_key)["root"])
    open_list = list(dict.fromkeys(generate_meta_file_paths(path_list)))
    trimmed_pending = (pending_message or "").strip()
    change_id = "New" if trimmed_pending else "default"
    change_msg = build_change_message(open_msg, pending_message)
    P4Tool.p4_add_to_changelist(open_list, change_id, change_msg)

    print(f"分支 {branch_key} 路径摘要: {summarize_paths_for_log(path_list)}")
    if change_id == "default":
        print("已加入默认 pending。")
    else:
        print("已加入新建 pending。")
        print(f"pending 描述: {change_msg}")
    return "已加入Pending（请在P4中确认）"


def apply_operation(paths: List[str], source_branch: str, target_branch: str, operation: str):
    if operation == "delete":
        for path in paths:
            target_path = get_branch_path(target_branch, path)
            delete_target_path(target_path)
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
    records: List[Dict[str, Any]] = []
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
        print(f"[预演] 源分支={source_branch} 目标分支={','.join(target_branches)} 操作={op}")
        print(f"[预演] 文件摘要: {summarize_paths_for_log(paths)}")
        print(f"[预演] 文件数量: {len(paths)}")
        if open_only or (no_submit and pending_message):
            print("[预演] 将打开到 Pending（--open-only）。")
            if pending_message:
                print(f"[预演] 追加说明: {pending_message}")
                print("[预演] 描述格式: p4-bypass p4-admin-bypass <默认说明> <pending-message>")
        elif no_submit:
            print("[预演] 将跳过提交（--no-submit）。")
        elif pending_message:
            print(f"[预演] 追加说明: {pending_message}")
            print("[预演] 提交描述格式: p4-bypass p4-admin-bypass <默认说明> <pending-message>")
        return records

    for target_branch in target_branches:
        if op != "delete":
            update_multiple_paths(paths, source_branch, "p4_update_log.txt")
        update_multiple_paths(paths, target_branch, "p4_update_log.txt")

        apply_operation(paths, source_branch, target_branch, op)

        if open_only:
            default_msg = f"open {op}: {source_branch} -> {target_branch}"
            change_msg = build_change_message(submit_message or default_msg, pending_message)
            open_status = open_multiple_paths(
                paths,
                target_branch,
                "p4_update_log.txt",
                submit_message or default_msg,
                pending_message=pending_message,
            )
            records.append(
                {
                    "branch": target_branch,
                    "action": "仅打开Pending",
                    "message": change_msg,
                    "status": open_status,
                    "paths": list(paths),
                }
            )
            continue

        if no_submit:
            if pending_message:
                default_msg = f"open {op}: {source_branch} -> {target_branch}"
                change_msg = build_change_message(submit_message or default_msg, pending_message)
                open_status = open_multiple_paths(
                    paths,
                    target_branch,
                    "p4_update_log.txt",
                    submit_message or default_msg,
                    pending_message=pending_message,
                )
                records.append(
                    {
                        "branch": target_branch,
                        "action": "仅打开Pending（由no-submit触发）",
                        "message": change_msg,
                        "status": open_status,
                        "paths": list(paths),
                    }
                )
            else:
                print(f"已跳过提交（--no-submit）: {source_branch} -> {target_branch}")
                records.append(
                    {
                        "branch": target_branch,
                        "action": "跳过提交",
                        "message": f"跳过提交: {source_branch} -> {target_branch}",
                        "status": "已跳过提交",
                        "paths": list(paths),
                    }
                )
            continue

        default_msg = f"sync {op}: {source_branch} -> {target_branch}"
        commit_msg = build_change_message(submit_message or default_msg, pending_message)
        submit_status = submit_multiple_paths(paths, target_branch, "p4_update_log.txt", commit_msg)
        records.append(
            {
                "branch": target_branch,
                "action": "提交",
                "message": commit_msg,
                "status": submit_status,
                "paths": list(paths),
            }
        )

    return records


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
    parser.add_argument("--pending-message", default=None, help="追加说明；描述统一格式为 p4-bypass p4-admin-bypass + 默认说明 + 该内容")
    parser.add_argument("--email", default=None, help="可选：将执行日志发送到该邮箱")
    parser.add_argument("--dry-run", action="store_true", help="仅打印将要执行的步骤，不实际执行")
    args = parser.parse_args()

    set_active_config(args.config)

    target_branches = parse_csv_values(args.branches)
    raw_paths = parse_csv_values(args.files)
    normalized_paths = [normalize_repo_path(p) for p in raw_paths if normalize_repo_path(p)]

    run_records = run_branch_sync(
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

    if args.email:
        email_subject = build_change_message(
            f"执行报告 {args.operation}: {args.source} -> {','.join(target_branches)}",
            args.pending_message,
        )
        email_body = build_email_report(
            records=run_records,
            source_branch=args.source,
            target_branches=target_branches,
            operation=args.operation,
            pending_message=args.pending_message,
        )
        if args.dry_run:
            print(f"预演模式不发送消息，目标邮箱: {args.email}")
        else:
            send_email_report(args.email, email_subject, email_body)
