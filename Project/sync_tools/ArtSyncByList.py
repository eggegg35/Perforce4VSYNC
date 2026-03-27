import argparse

import ArtSyncMultiBranch


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run branch sync with file list')
    parser.add_argument('--list-file', required=True, help='鍒楄〃鏂囦欢璺緞锛堟瘡琛屼竴涓浉瀵硅矾寰勶級')
    parser.add_argument('--branches', required=True, help='鐩爣鍒嗘敮锛岃嫳鏂囬€楀彿鍒嗛殧锛屼緥濡? 001,feature')
    parser.add_argument('--operation', required=True, choices=['add', 'modify', 'delete'], help='鏂囦欢鎿嶄綔绫诲瀷')
    parser.add_argument('--source', default=ArtSyncMultiBranch.DEFAULT_SOURCE_BRANCH, help='婧愬垎鏀紝榛樿 art')
    parser.add_argument('--config', default=ArtSyncMultiBranch.DEFAULT_CONFIG_PATH, help='鍒嗘敮閰嶇疆 JSON 璺緞')
    parser.add_argument('--message', default=None, help='Optional submit message')
    parser.add_argument('--no-submit', action='store_true', help='鍙洿鏂?鎷疯礉/鍒犻櫎锛屼笉鎵ц鎻愪氦')
    parser.add_argument('--open-only', action='store_true', help='鍙墦寮€鍒?pending锛屼笉鎻愪氦')
    parser.add_argument('--pending-message', default=None, help='Extra text for changelist description, format: p4-p4 + default message + pending-message')
    parser.add_argument('--email', default=None, help='Optional: send execution log to this email')
    parser.add_argument('--dry-run', action='store_true', help='浠呮墦鍗板皢瑕佹墽琛岀殑姝ラ锛屼笉瀹為檯鎵ц')
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

