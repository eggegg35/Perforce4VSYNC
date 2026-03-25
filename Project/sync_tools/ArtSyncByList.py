import argparse

import ArtSyncMultiBranch


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="按列表文件执行分支同步")
    parser.add_argument("--list-file", required=True, help="列表文件路径（每行一个相对路径）")
    parser.add_argument("--branches", required=True, help="目标分支，英文逗号分隔。例如: 001,feature")
    parser.add_argument("--operation", required=True, choices=["add", "modify", "delete"], help="文件操作类型")
    parser.add_argument("--source", default=ArtSyncMultiBranch.DEFAULT_SOURCE_BRANCH, help="源分支，默认 art")
    parser.add_argument("--config", default=ArtSyncMultiBranch.DEFAULT_CONFIG_PATH, help="分支配置 JSON 路径")
    parser.add_argument("--message", default=None, help="可选提交说明")
    parser.add_argument("--no-submit", action="store_true", help="只更新+拷贝/删除，不执行提交")
    parser.add_argument("--open-only", action="store_true", help="只打开到默认 pending，不提交")
    parser.add_argument("--pending-message", default=None, help="仅 --open-only 时有效：创建新 pending 并使用该说明")
    parser.add_argument("--dry-run", action="store_true", help="仅打印将要执行的步骤，不实际执行")
    args = parser.parse_args()

    ArtSyncMultiBranch.set_active_config(args.config)
    paths_string = ArtSyncMultiBranch.process_file(args.list_file)
    paths = ArtSyncMultiBranch.parse_csv_values(paths_string)

    ArtSyncMultiBranch.run_branch_sync(
        target_branches=ArtSyncMultiBranch.parse_csv_values(args.branches),
        paths=paths,
        operation=args.operation,
        source_branch=args.source,
        submit_message=args.message,
        no_submit=args.no_submit,
        open_only=args.open_only,
        pending_message=args.pending_message,
        dry_run=args.dry_run,
    )
