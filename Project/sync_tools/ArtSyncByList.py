import argparse

import ArtSyncMultiBranch


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='按列表文件执行分支同步')
    parser.add_argument('--list-file', required=True, help='列表文件路径（每行一个相对路径）')
    parser.add_argument('--branches', required=True, help='目标分支，英文逗号分隔，例如: 001,feature')
    parser.add_argument('--operation', required=True, choices=['add', 'modify', 'delete'], help='文件操作类型')
    parser.add_argument('--source', default=ArtSyncMultiBranch.DEFAULT_SOURCE_BRANCH, help='源分支，默认 art')
    parser.add_argument('--config', default=ArtSyncMultiBranch.DEFAULT_CONFIG_PATH, help='分支配置 JSON 路径')
    parser.add_argument('--message', default=None, help='可选提交说明')
    parser.add_argument('--no-submit', action='store_true', help='只更新+拷贝/删除，不执行提交')
    parser.add_argument('--open-only', action='store_true', help='只打开到 pending，不提交')
    parser.add_argument('--pending-message', default=None, help='追加说明；描述统一格式为 p4-p4 + 默认说明 + 该内容')
    parser.add_argument('--email', default=None, help='可选：将执行日志发送到该邮箱')
    parser.add_argument('--dry-run', action='store_true', help='仅打印将要执行的步骤，不实际执行')
    args = parser.parse_args()

    ArtSyncMultiBranch.set_active_config(args.config)
    paths_string = ArtSyncMultiBranch.process_file(args.list_file)
    paths = ArtSyncMultiBranch.parse_csv_values(paths_string)
    target_branches = ArtSyncMultiBranch.parse_csv_values(args.branches)

    run_records = ArtSyncMultiBranch.run_branch_sync(
        target_branches=target_branches,
        paths=paths,
        operation=args.operation,
        source_branch=args.source,
        submit_message=args.message,
        no_submit=args.no_submit,
        open_only=args.open_only,
        pending_message=args.pending_message,
        dry_run=args.dry_run,
    )

    if args.email:
        email_subject = ArtSyncMultiBranch.build_change_message(
            f"\u6267\u884c\u62a5\u544a {args.operation}: {args.source} -> {','.join(target_branches)}",
            args.pending_message,
        )
        email_body = ArtSyncMultiBranch.build_email_report(
            records=run_records,
            source_branch=args.source,
            target_branches=target_branches,
            operation=args.operation,
            pending_message=args.pending_message,
        )
        if args.dry_run:
            print(f'\u9884\u6f14\u6a21\u5f0f\u4e0d\u53d1\u9001\u6d88\u606f\uff0c\u76ee\u6807\u90ae\u7bb1: {args.email}')
        else:
            ArtSyncMultiBranch.send_email_report(args.email, email_subject, email_body)
