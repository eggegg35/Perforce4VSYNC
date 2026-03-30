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
from MinIODownloadByConfig import ExecutionDownloadWithConfig

BASE_DIR = SCRIPT_DIR
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "branches.json")
DEFAULT_SOURCE_BRANCH = "art"
DEFAULT_MSG_API = "http://10.8.45.67:3106/lark_tools_send_msg"
DEFAULT_TXT_DOWNLOAD_DIR = r"C:\Git\Perforce4VSYNC\Project\List"
REQUIRED_BRANCH_FIELDS = ("root", "workspace", "p4_user")


def _safe_print(message: str):
    text = str(message)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(text)
    except UnicodeEncodeError:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))
        else:
            print(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))

_ACTIVE_CONFIG = None


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if "branches" not in data:
        raise ValueError("Config must contain a branches field.")
    return data


def set_active_config(config_path: str = DEFAULT_CONFIG_PATH):
    global _ACTIVE_CONFIG
    _ACTIVE_CONFIG = load_config(config_path)


def get_branch_config(branch_key: str) -> dict:
    if _ACTIVE_CONFIG is None:
        set_active_config(DEFAULT_CONFIG_PATH)
    branches = _ACTIVE_CONFIG.get("branches", {})
    if branch_key not in branches:
        raise ValueError(f"閰嶇疆涓笉瀛樺湪鍒嗘敮: {branch_key}")
    return branches[branch_key]


def validate_branch_config(branch_key: str):
    branch_cfg = get_branch_config(branch_key)
    for field in REQUIRED_BRANCH_FIELDS:
        value = str(branch_cfg.get(field, "")).strip()
        if not value:
            raise ValueError(
                f"鍒嗘敮 {branch_key} 鐨勯厤缃」 {field} 涓虹┖锛岃鍏堟洿鏂伴厤缃枃浠? {DEFAULT_CONFIG_PATH}"
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
        _safe_print(f"璇诲彇鍒楄〃鏂囦欢澶辫触: {e}")
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
            _safe_print(f"鍒犻櫎鏂囦欢澶辫触: {file_path}, 閿欒: {e}")


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
        _safe_print(f"鎷疯礉鏂囦欢澶辫触: {src_file} -> {dst_file}, 閿欒: {e}")


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
            _safe_print(f"鍒犻櫎鐩綍澶辫触: {path}, 閿欒: {e}")
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
    full_msg = f"p4-p4 {base_msg}"
    trimmed_pending = (pending_message or "").strip()
    if trimmed_pending:
        full_msg = f"{full_msg} {trimmed_pending}"
    return full_msg


def summarize_paths_for_log(paths: List[str], max_chars: int = 140) -> str:
    valid_paths = [p for p in paths if p]
    if not valid_paths:
        return "no files"

    joined = ", ".join(valid_paths)
    if len(joined) <= max_chars:
        return joined

    if len(valid_paths) == 1:
        return valid_paths[0]

    return f"{valid_paths[0]} and {len(valid_paths) - 1} more files"


def submit_multiple_paths(paths: List[str], branch_key: str, log_file: str, submit_msg: str) -> str:
    setup_p4_args(branch_key, log_file)
    path_list = build_unlocal_paths(paths, root_prefix=get_branch_config(branch_key)["root"])
    sub_list = generate_meta_file_paths(path_list)
    result = P4Tool.p4_commitpathlist(sub_list, commmitMsg=submit_msg)
    _safe_print(f"Submit path summary: {summarize_paths_for_log(path_list)}")
    if result is True:
        _safe_print(f"Branch {branch_key} submit success.")
        return "success"
    if result is False:
        _safe_print(f"Branch {branch_key} not submitted (possibly no changelist content).")
        return "not_submitted"
    _safe_print(f"Branch {branch_key} submit failed, please check p4 logs.")
    return "failed"


def build_email_report(
    records: List[Dict[str, Any]],
    source_branch: str,
    target_branches: List[str],
    operation: str,
    pending_message: str = None,
) -> str:
    status_map = {
        "success": "\u6210\u529f",
        "not_submitted": "\u672a\u63d0\u4ea4",
        "failed": "\u5931\u8d25",
        "skipped": "\u5df2\u8df3\u8fc7",
    }

    lines = [
        "ArtSync \u6267\u884c\u62a5\u544a",
        f"\u65f6\u95f4: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\u6e90\u5206\u652f: {source_branch}",
        f"\u76ee\u6807\u5206\u652f: {','.join(target_branches)}",
        f"\u64cd\u4f5c\u7c7b\u578b: {operation}",
    ]
    if pending_message:
        lines.append(f"\u8ffd\u52a0\u8bf4\u660e: {pending_message}")
    lines.append("")
    lines.append("\u6267\u884c\u8bb0\u5f55:")

    if not records:
        lines.append("- \u65e0\u8bb0\u5f55")
    else:
        for record in records:
            status_value = str(record.get("status", ""))
            status_text = status_map.get(status_value, status_value)
            lines.append(
                f"- \u5206\u652f={record.get('branch', '')} \u52a8\u4f5c={record.get('action', '')} \u72b6\u6001={status_text} \u8bf4\u660e={record.get('message', '')}"
            )
            path_summary = summarize_paths_for_log(record.get("paths", []))
            lines.append(f"  \u6587\u4ef6\u6458\u8981: {path_summary}")
            lines.append(f"  \u6587\u4ef6\u6570\u91cf: {len(record.get('paths', []))}")
            lines.append("  \u5907\u6ce8: \u5df2\u81ea\u52a8\u5904\u7406\u5bf9\u5e94 .meta")

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
        _safe_print(f"\u6d88\u606f\u5df2\u53d1\u9001\u5230\u90ae\u7bb1: {to_email}, \u8fd4\u56de: {ret}")
        return True
    except urllib.error.HTTPError as e:
        _safe_print(f"\u6d88\u606f\u53d1\u9001\u5931\u8d25: HTTP {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        _safe_print(f"\u6d88\u606f\u53d1\u9001\u5931\u8d25: {e.reason}")
        return False
    except Exception as e:
        _safe_print(f"\u6d88\u606f\u53d1\u9001\u5931\u8d25: {e}")
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

    _safe_print(f"\u5206\u652f {branch_key} \u8def\u5f84\u6458\u8981: {summarize_paths_for_log(path_list)}")
    if change_id == "default":
        _safe_print("\u5df2\u52a0\u5165\u9ed8\u8ba4 pending\u3002")
    else:
        _safe_print("\u5df2\u52a0\u5165\u65b0\u5efa pending\u3002")
        _safe_print(f"pending \u63cf\u8ff0: {change_msg}")
    return "\u5df2\u52a0\u5165 pending\uff08\u8bf7\u5728 P4 \u4e2d\u786e\u8ba4\uff09"



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
        _safe_print("Error: at least one sync path is required.")
        sys.exit(1)

    op = operation.lower()
    if op not in ("add", "modify", "delete"):
        _safe_print("閿欒: operation 浠呮敮鎸?add / modify / delete")
        sys.exit(1)

    if dry_run:
        _safe_print(f"[棰勬紨] 婧愬垎鏀?{source_branch} 鐩爣鍒嗘敮={','.join(target_branches)} 鎿嶄綔={op}")
        _safe_print(f"[棰勬紨] 鏂囦欢鎽樿: {summarize_paths_for_log(paths)}")
        _safe_print(f"[棰勬紨] 鏂囦欢鏁伴噺: {len(paths)}")
        if open_only or (no_submit and pending_message):
            _safe_print("[DRY-RUN] Will open files to pending (--open-only).")
            if pending_message:
                _safe_print(f"[棰勬紨] 杩藉姞璇存槑: {pending_message}")
                _safe_print("[棰勬紨] 鎻忚堪鏍煎紡: p4-p4 <榛樿璇存槑> <pending-message>")
        elif no_submit:
            _safe_print("[DRY-RUN] Will skip submit (--no-submit).")
        elif pending_message:
            _safe_print(f"[棰勬紨] 杩藉姞璇存槑: {pending_message}")
            _safe_print("[棰勬紨] 鎻愪氦鎻忚堪鏍煎紡: p4-p4 <榛樿璇存槑> <pending-message>")
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
                    "action": "浠呮墦寮€Pending",
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
                        "action": "open_pending_by_no_submit",
                        "message": change_msg,
                        "status": open_status,
                        "paths": list(paths),
                    }
                )
            else:
                _safe_print(f"Skipped submit (--no-submit): {source_branch} -> {target_branch}")
                records.append(
                    {
                        "branch": target_branch,
                        "action": "skip_submit",
                        "message": f"Skip submit: {source_branch} -> {target_branch}",
                        "status": "skipped",
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
                "action": "submit",
                "message": commit_msg,
                "status": submit_status,
                "paths": list(paths),
            }
        )

    return records


def parse_csv_values(raw: str) -> List[str]:
    return [p.strip() for p in raw.split(",") if p.strip()]


def resolve_paths_from_args(files_arg: str = None, txtname_arg: str = None) -> List[str]:
    files_text = (files_arg or "").strip()
    txtname = (txtname_arg or "").strip()

    if files_text and txtname:
        _safe_print("Error: use only one of --files or --txtname.")
        sys.exit(1)

    if not files_text and not txtname:
        _safe_print("Error: either --files or --txtname is required.")
        sys.exit(1)

    if files_text:
        raw_paths = parse_csv_values(files_text)
        normalized = [normalize_repo_path(p) for p in raw_paths if normalize_repo_path(p)]
        if not normalized:
            _safe_print("Error: --files does not contain valid paths.")
            sys.exit(1)
        return normalized

    download_code = ExecutionDownloadWithConfig(
        object_name=txtname,
        output_path=DEFAULT_TXT_DOWNLOAD_DIR,
    )
    if download_code != 0:
        _safe_print(f"Error: download txt from MinIO failed, code={download_code}")
        sys.exit(download_code)

    local_txt_path = os.path.join(DEFAULT_TXT_DOWNLOAD_DIR, os.path.basename(txtname))
    paths_text = process_file(local_txt_path)
    if not paths_text:
        _safe_print(f"Error: no valid sync path found in txt: {local_txt_path}")
        sys.exit(1)

    raw_paths = parse_csv_values(paths_text)
    normalized = [normalize_repo_path(p) for p in raw_paths if normalize_repo_path(p)]
    if not normalized:
        _safe_print(f"Error: no valid sync path after normalization: {local_txt_path}")
        sys.exit(1)
    return normalized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync files from Art branch to target branches")
    parser.add_argument("--branches", required=True, help="Target branches, comma separated, e.g. 001,feature")
    parser.add_argument("--files", required=False, help="Sync files or folders, comma separated")
    parser.add_argument("--txtname", required=False, help="MinIO list txt object name; downloaded into C:\\Git\\Perforce4VSYNC\\Project\\List")
    parser.add_argument("--operation", required=True, choices=["add", "modify", "delete"], help="File operation type")
    parser.add_argument("--source", default=DEFAULT_SOURCE_BRANCH, help="Source branch, default art")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Branch config JSON path")
    parser.add_argument("--message", default=None, help="Optional submit message")
    parser.add_argument("--no-submit", action="store_true", help="Do sync action but skip submit")
    parser.add_argument("--open-only", action="store_true", help="Only open files to pending, do not submit")
    parser.add_argument("--pending-message", default=None, help="Extra text for changelist description, format: p4-p4 + default message + pending-message")
    parser.add_argument("--email", default=None, help="Optional: send execution log to this email")
    parser.add_argument("--dry-run", action="store_true", help="Print actions only, do not execute")
    args = parser.parse_args()

    set_active_config(args.config)

    target_branches = parse_csv_values(args.branches)
    normalized_paths = resolve_paths_from_args(files_arg=args.files, txtname_arg=args.txtname)

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
            f"\u6267\u884c\u62a5\u544a {args.operation}: {args.source} -> {','.join(target_branches)}",
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
            _safe_print(f"\u9884\u6f14\u6a21\u5f0f\u4e0d\u53d1\u9001\u6d88\u606f\uff0c\u76ee\u6807\u90ae\u7bb1: {args.email}")
        else:
            send_email_report(args.email, email_subject, email_body)

