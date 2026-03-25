import os
import shutil
import sys

def copy_asset(src_asset: str, dst_asset: str):
    """
    复制单个资产文件及其 .meta 文件，自动创建目录、处理只读文件、覆盖旧文件
    """
    def safe_copy_file(src: str, dst: str):
        try:
            if not os.path.isfile(src):
                print(f"源文件不存在: {src}")
                return
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                os.chmod(dst, 0o666)  # 解除只读
                os.remove(dst)
            shutil.copy2(src, dst)
            # print(f"已复制: {src} -> {dst}")
        except Exception as e:
            print(f"复制失败: {src} -> {dst}，错误: {e}")

    # 复制主文件
    safe_copy_file(src_asset, dst_asset)

    # 复制 .meta 文件（如果存在）
    src_meta = src_asset + ".meta"
    dst_meta = dst_asset + ".meta"
    # if os.path.isfile(src_meta):
    #     safe_copy_file(src_meta, dst_meta)
    safe_copy_file(src_meta, dst_meta)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python copy_asset.py <源资产文件> <目标资产文件>")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]
    copy_asset(src, dst)
