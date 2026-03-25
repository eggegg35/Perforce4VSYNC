import os
import shutil
import sys
import stat

def clear_folder(folder_path: str):
    """
    删除指定文件夹内的所有内容，但保留文件夹本身，自动解除只读限制
    """
    if not os.path.exists(folder_path):
        print(f"Release路径不存在: {folder_path}")
        return

    if not os.path.isdir(folder_path):
        print(f"不是文件夹: {folder_path}")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.chmod(item_path, stat.S_IWRITE)  # 解除只读
                os.remove(item_path)
                # print(f"已删除文件: {item_path}")
            elif os.path.isdir(item_path):
                def on_rm_error(func, path, exc_info):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(item_path, onerror=on_rm_error)
                # print(f"已删除文件夹: {item_path}")
        except Exception as e:
            print(f"删除失败: {item_path}，错误: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python clear_folder.py <文件夹路径>")
        sys.exit(1)

    target_folder = sys.argv[1]
    clear_folder(target_folder)
