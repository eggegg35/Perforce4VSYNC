import os
import shutil
import sys
from pathlib import Path

def copy_folder(src_folder: str, dst_folder: str):
    """
    将 src_folder 内的所有内容复制到 dst_folder，支持递归、覆盖、处理只读文件
    """
    src_path = Path(src_folder)
    dst_path = Path(dst_folder)

    if not src_path.exists():
        print(f"源文件夹不存在: {src_folder}")
        return

    if not src_path.is_dir():
        print(f"源路径不是文件夹: {src_folder}")
        return

    # 创建目标文件夹
    dst_path.mkdir(parents=True, exist_ok=True)

    for item in src_path.iterdir():
        target_path = dst_path / item.name

        try:
            if item.is_dir():
                # 递归复制子目录
                copy_folder(item, target_path)
            else:
                # 复制文件，处理只读和已存在的目标
                if target_path.exists():
                    target_path.chmod(0o666)  # 修改文件权限
                    target_path.unlink()  # 删除文件
                shutil.copy2(item, target_path)
                # print(f"已复制文件: {item} -> {target_path}")
        except Exception as e:
            print(f"复制失败: {item} -> {target_path}，错误: {e}")



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python copy_folder.py <源文件夹路径> <目标文件夹路径>")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]
    copy_folder(src, dst)
