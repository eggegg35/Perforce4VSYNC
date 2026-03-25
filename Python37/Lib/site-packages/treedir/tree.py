"""
小小明的代码
CSDN主页：https://blog.csdn.net/as604049322
"""

import os

import rich
from rich.text import Text
from rich.tree import Tree


def get_file_size(file):
    try:
        return os.path.getsize(file)
    except:
        pass


def format_file_size(size):
    if size is None:
        return "无权限"
    num = 0
    while size > 1024:
        size /= 1024
        num += 1
    unit = ["b", "KB", "MB", "GB", "TB"]
    return f"{size:.2f}".rstrip(".0").zfill(1) + unit[num]


def walk_dir(path, tree, level=0) -> int:
    global max_level, no_recursion_calc
    try:
        listdir = os.listdir(path)
    except:
        return 0
    total_size = 0
    for file in listdir:
        if no_recursion_calc and level >= max_level:
            continue
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            parent = None
            if level < max_level:
                parent = tree.add(f"[bold magenta]{file}")
            size = walk_dir(file_path, parent, level + 1)
            if size and parent:
                parent.label += f"[bold yellow] ({format_file_size(size)})"
        else:
            size = get_file_size(file_path)
            if level < max_level:
                text_filename = Text(file, "green")
                text_filename.highlight_regex(r"\.[^.]+$", "bold red")
                text_filename.append(
                    f" ({format_file_size(size)})", "bold blue")
                tree.add(text_filename)
        if size:
            total_size += size
    return total_size


max_level = None
no_recursion_calc = None


def tree_dir(path, m_level=7, no_calc=False):
    global max_level, no_recursion_calc
    max_level = m_level
    no_recursion_calc = no_calc
    tree = Tree(f"[bold magenta]{os.path.abspath(path)}")
    size = walk_dir(path, tree)
    tree.label += f" [bold yellow]({format_file_size(size)})"
    rich.print(tree)
    if no_calc:
        rich.print("[bold red]注意：取消了递归计算文件夹大小，仅显示遍历到的文件总大小")
