import os
import types
import P4Tool

import argparse
import sys

from clear_folder import clear_folder
from clear_asset import clear_asset
from copy_folder import copy_folder
from copy_asset import copy_asset

# Workspace and depot paths
RELEASE_ROOT = r"E:\worldx_robot_HZPCC0420018_2708"
VER001_ROOT = r"C:\worldx_robot_HZPCC0420018_1001"

RELEASE_WORKSPACE = r"worldx_robot_HZPCC0420018_2708"
VER001_WORKSPACE = r"worldx_robot_HZPCC0420018_1001"

VER001_DEPOT = r"//world_x/ver_0.01"
RELEASE_DEPOT = r"//world_x/release"

def to_windows_path(path: str) -> str:
    return path.replace("/", "\\")

def get_release_path(user_path: str):
    return os.path.join(RELEASE_ROOT, user_path)

def get_ver001_path(user_path: str):
    return os.path.join(VER001_ROOT, user_path)

def get_release_depot_path(user_path: str):
    return os.path.join(RELEASE_DEPOT, user_path)

def get_ver001_depot_path(user_path: str):
    return os.path.join(VER001_DEPOT, user_path)

def process_file(file_path):
    try:
        with open(file_path, 'r') as file:
            # 读取文件内容，去除换行符并加上前缀
            paths = [f"unity_project/{line.strip()}" for line in file if line.strip()]
            # 用英文逗号连接每个路径
            result = ', '.join(paths)
            return result
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def is_unity_folder(path: str) -> bool:
    path = os.path.normpath(path)
    name = os.path.basename(path)
    if os.path.exists(path):
        return os.path.isdir(path)
    return "." not in name

def get_asset_directory(asset_path: str) -> str:
    asset_path = os.path.normpath(asset_path)
    return os.path.dirname(asset_path)

def copy001torls(target_path: str):
    ver001_path = get_ver001_path(target_path)
    release_path = get_release_path(target_path)
    if not is_unity_folder(release_path):
        clear_asset(release_path)
    else:
        clear_folder(release_path)

    if not is_unity_folder(ver001_path):
        copy_asset(ver001_path,release_path)
    else:
        copy_folder(ver001_path, release_path)


def generate_meta_file_paths(input_list):
    output_list = []
    for file_path in input_list:
        # 添加原始文件路径
        output_list.append(file_path)
        # 生成对应的 .meta 文件路径
        meta_file_path = f"{file_path}.meta"
        output_list.append(meta_file_path)
    return output_list

def copy001torlspaths(paths_string: str):
    # 拆分路径
    path_list = [p.strip() for p in paths_string.split(",") if p.strip()]
    for path in path_list:
        copy001torls(to_windows_path(path))
        # print(f"正在覆盖：{to_windows_path(path)}")

def get_parent_path(path: str) -> str:
    """
    返回给定路径的上一级路径，自动处理 / 和 \ 混用
    """
    # 统一为系统路径格式
    normalized = path.replace("\\", "/").rstrip("/")
    parent = os.path.dirname(normalized)
    return parent

def update_multiple_paths(path_string: str, p4user: str, p4workspace: str, log_file: str, rls:bool):
    # 构造 args
    P4Tool.args = types.SimpleNamespace()
    P4Tool.args.p4user = p4user
    P4Tool.args.p4workspace = p4workspace
    P4Tool.args.logFile = log_file
    P4Tool.args.retLogFile = log_file
    setattr(P4Tool, 'args', P4Tool.args)
    # 拆分路径
    path_list = [p.strip() for p in path_string.split(",") if p.strip()]
    #
    #
    # if rls:
    #     P4Tool.p4_update(RELEASE_ROOT)
    # else:
    #     P4Tool.p4_update(VER001_ROOT)

    # 遍历调用 p4_update
    for path in path_list:
        # print(f"正在更新：{path}")
        if rls:
            P4Tool.p4_update(get_parent_path(get_release_path(path)))
        else:
            P4Tool.p4_update(get_parent_path(get_ver001_path(path)))

def update_multiple_001_paths(path_string: str):
    update_multiple_paths(
        path_string,
        p4user="worldx_robot",
        p4workspace=VER001_WORKSPACE,
        log_file="p4_update_log.txt",
        rls=False
    )

def update_multiple_rls_paths(path_string: str):
    update_multiple_paths(
        path_string,
        p4user="worldx_robot",
        p4workspace=RELEASE_WORKSPACE,
        log_file="p4_update_log.txt",
        rls=True
    )
def build_unlocal_paths(path_string: str, root_prefix: str) -> list:
    # 清理 root_prefix 尾部的斜杠
    root_prefix = root_prefix.rstrip("\\/")
    # 拆分路径并标准化为当前系统格式
    path_list = [p.strip().replace("/", os.sep).replace("\\", os.sep) for p in path_string.split(",") if p.strip()]
    # 拼接完整路径
    full_paths = [os.path.join(root_prefix, p) for p in path_list]
    return full_paths
def build_local_paths(path_string: str, root_prefix: str) -> list:
    # 清理 root_prefix 尾部的斜杠并统一为 /
    root_prefix = root_prefix.rstrip("\\/").replace("\\", "/")
    # 拆分路径并统一为 /
    path_list = [p.strip().replace("\\", "/") for p in path_string.split(",") if p.strip()]
    # 拼接完整路径并统一为 /
    full_paths = [f"{root_prefix}/{p}" for p in path_list]
    return full_paths


def submit_multiple_paths(path_string: str, p4user: str, p4workspace: str, log_file: str, rls:bool, dir: str = "p4-bypass p4-admin-bypass 001 To release "):
    # 构造 args
    P4Tool.args = types.SimpleNamespace()
    P4Tool.args.p4user = p4user
    P4Tool.args.p4workspace = p4workspace
    P4Tool.args.logFile = log_file
    P4Tool.args.retLogFile = log_file
    setattr(P4Tool, 'args', P4Tool.args)
    if rls:
        path_list = build_unlocal_paths(path_string, root_prefix=RELEASE_ROOT)
        sub_list = generate_meta_file_paths(path_list)
        P4Tool.p4_commitpathlist(sub_list, commmitMsg=dir)
        print(f"以提交：{path_list}")

def submitreleasepaths(path_str: str, indir: str = "p4-bypass p4-admin-bypass 001 To release "):
    submit_multiple_paths(
        path_str,
        p4user="worldx_robot",
        p4workspace=RELEASE_WORKSPACE,
        log_file="p4_update_log.txt",
        rls=True,
        dir = indir
    )

def run_release_pipeline(paths_string, dir: str = "001 To release "):
    # 清理空格并拆分路径
    raw_paths = [p.strip() for p in paths_string.split(",")]
    cleaned_paths = [p for p in raw_paths if p]

    # 加锁：路径为空或非法
    if not cleaned_paths:
        print("错误：路径列表为空或格式非法（可能包含连续逗号或空项）")
        sys.exit(1)

    # 重新拼接为合法字符串传入各函数
    cleaned_path_string = ",".join(cleaned_paths)

    update_multiple_001_paths(cleaned_path_string)
    update_multiple_rls_paths(cleaned_path_string)
    copy001torlspaths(cleaned_path_string)
    submitreleasepaths(cleaned_path_string,dir)

def run_release_pipeline_list(txtpath_string, dir: str = "list 001 To release "):
    # 重新拼接为合法字符串传入各函数
    cleaned_path_string = process_file(txtpath_string)

    update_multiple_001_paths(cleaned_path_string)
    update_multiple_rls_paths(cleaned_path_string)
    copy001torlspaths(cleaned_path_string)
    submitreleasepaths(cleaned_path_string,dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步 ver_0.01 到 release")
    parser.add_argument("--paths", help="用英文逗号分隔的多个相对路径（相对于工作区根目录）")
    args = parser.parse_args()

    run_release_pipeline(args.paths)

