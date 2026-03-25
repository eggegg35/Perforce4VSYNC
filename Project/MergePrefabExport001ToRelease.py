import os
import argparse

import Merge001ToRelease


ROOT001 = r"C:\worldx_robot_HZPCC0420018_1001\unity_project"

def to_absolute_unity_path(relative_path, project_root):
    normalized = relative_path.replace("/", os.sep)
    return os.path.normpath(os.path.join(project_root, normalized))

def extract_export_files(prefab_path):
    # 提取 prefab 名字（不带扩展名）
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
                        export_paths.append(f"unity_project/{path}")
                    elif not stripped.startswith(" "):  # 结束 exportFiles 块
                        break

        # 拼接字符串（返回值用逗号分隔）
        result = ",".join(export_paths)

        # 写入文件（每行一个路径）
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as out:
            out.write("\n".join(export_paths))

        print(f"导出成功：{output_file}")
        return result

    except Exception as e:
        print(f"处理失败：{e}")
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步 ver_0.01 到 release")
    parser.add_argument("--paths", help="用英文逗号分隔的多个相对路径（相对于工作区根目录）")
    args = parser.parse_args()
    Merge001ToRelease.update_multiple_001_paths(to_absolute_unity_path(args.paths, ROOT001))
    export_str = extract_export_files(to_absolute_unity_path(args.paths, ROOT001))
    Merge001ToRelease.run_release_pipeline(export_str, "001 To release Export Prefab:" + os.path.splitext(os.path.basename(args.paths))[0])
