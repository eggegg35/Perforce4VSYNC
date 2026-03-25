import os
import stat
import sys

def clear_asset(asset_file: str):
    """
    删除指定资产文件及其 .meta 文件，自动解除只读限制
    """
    def safe_delete(file_path: str):
        if os.path.isfile(file_path):
            try:
                os.chmod(file_path, stat.S_IWRITE)  # 解除只读限制
                os.remove(file_path)
                # print(f"已删除: {file_path}")
            except PermissionError:
                print(f"权限不足，无法删除: {file_path}（可能被占用或只读）")
            except Exception as e:
                print(f"删除失败: {file_path}，错误: {e}")
        else:
            print(f"新增文件: {file_path}")

    safe_delete(asset_file)
    safe_delete(asset_file + ".meta")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python clear_asset.py <资产文件路径>")
        sys.exit(1)

    target_asset = sys.argv[1]
    clear_asset(target_asset)
