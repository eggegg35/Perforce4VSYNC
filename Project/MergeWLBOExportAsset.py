import os
import argparse

import Merge001ToRelease

def generate_asset_paths(input_path: str) -> str:
    """
    根据输入路径生成三个完整资源路径字符串
    """
    input_path = input_path.strip().replace("\\", "/")
    map_name = os.path.basename(input_path)

    paths = [
        f"unity_project/Assets/Res/Level/LevelLayout/{map_name}",
        f"unity_project/AssetsExtra/raw/xrenderMobile/{map_name}",
        f"unity_project/AssetsExtra/raw/xrenderPc/{map_name}",
        f"unity_project/AssetsExtra/raw/xrender/{map_name}",
        f"unity_project/AssetsExtra/raw/XGIProbe/{map_name}",
        f"unity_project/Assets/Res_Export/XRenderMeshData/MB/CompressedMesh/{map_name}",
        f"unity_project/Assets/Res_Export/XRenderMeshData/PC/CompressedMesh/{map_name}"
    ]

    return ",".join(paths)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步 ver_0.01 到 release")
    parser.add_argument("--paths", help="用英文逗号分隔的多个相对路径（相对于工作区根目录）")
    args = parser.parse_args()
    mergepaths = generate_asset_paths(args.paths)
    print(mergepaths)
    Merge001ToRelease.run_release_pipeline(mergepaths, "001 To release Export scene:" + os.path.splitext(os.path.basename(args.paths))[0])
