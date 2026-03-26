import os
import argparse

import ArtSyncMultiBranch


def resolve_source_prefab_path(prefab_path: str, source_branch: str) -> str:
    source_root = ArtSyncMultiBranch.get_branch_config(source_branch)["root"]
    normalized = prefab_path.strip().replace("\\", "/")
    if normalized.startswith("unity_project/"):
        normalized = normalized[len("unity_project/"):]
    return os.path.normpath(os.path.join(source_root, "unity_project", normalized))


def extract_export_files(prefab_path: str) -> str:
    prefab_name = os.path.splitext(os.path.basename(prefab_path))[0]
    output_file = os.path.join(r"D:\PrefabMergeLog", f"{prefab_name}.txt")

    export_paths = []
    in_export_block = False

    try:
        with open(prefab_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("exportFiles:"):
                    in_export_block = True
                    continue
                if in_export_block:
                    if stripped.startswith("- "):
                        path = stripped[2:].strip()
                        export_paths.append(ArtSyncMultiBranch.normalize_repo_path(path))
                    elif not stripped.startswith(" "):
                        break

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as out:
            out.write("\n".join(export_paths))

        print(f"导出成功: {output_file}")
        return ",".join(export_paths)
    except Exception as e:
        print(f"处理失败: {e}")
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="读取Prefab导出列表并执行分支同步")
    parser.add_argument("--paths", required=True, help="Prefab相对路径（相对 unity_project）")
    parser.add_argument("--branches", required=True, help="目标分支，英文逗号分隔。例如: 001,feature")
    parser.add_argument("--operation", required=True, choices=["add", "modify", "delete"], help="文件操作类型")
    parser.add_argument("--source", default=ArtSyncMultiBranch.DEFAULT_SOURCE_BRANCH, help="源分支，默认 art")
    parser.add_argument("--config", default=ArtSyncMultiBranch.DEFAULT_CONFIG_PATH, help="分支配置 JSON 路径")
    parser.add_argument("--message", default=None, help="可选提交说明")
    parser.add_argument("--no-submit", action="store_true", help="只更新+拷贝/删除，不执行提交")
    parser.add_argument("--open-only", action="store_true", help="只打开到默认 pending，不提交")
    parser.add_argument("--pending-message", default=None, help="追加说明；描述统一格式为 p4-bypass p4-admin-bypass + 默认说明 + 该内容")
    parser.add_argument("--dry-run", action="store_true", help="仅打印将要执行的步骤，不实际执行")
    args = parser.parse_args()

    ArtSyncMultiBranch.set_active_config(args.config)
    prefab_abs_path = resolve_source_prefab_path(args.paths, args.source)
    export_str = extract_export_files(prefab_abs_path)

    ArtSyncMultiBranch.run_branch_sync(
        target_branches=ArtSyncMultiBranch.parse_csv_values(args.branches),
        paths=ArtSyncMultiBranch.parse_csv_values(export_str),
        operation=args.operation,
        source_branch=args.source,
        submit_message=args.message,
        no_submit=args.no_submit,
        open_only=args.open_only,
        pending_message=args.pending_message,
        dry_run=args.dry_run,
    )
