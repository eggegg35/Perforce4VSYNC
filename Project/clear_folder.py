import os
import shutil
import stat
import sys


def clear_folder(folder_path: str):
    """Remove all contents in a folder while keeping the folder itself."""
    if not os.path.exists(folder_path):
        print(f"PathNotFound: {folder_path}")
        return

    if not os.path.isdir(folder_path):
        print(f"NotAFolder: {folder_path}")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.chmod(item_path, stat.S_IWRITE)
                os.remove(item_path)
            elif os.path.isdir(item_path):
                def on_rm_error(func, path, exc_info):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)

                shutil.rmtree(item_path, onerror=on_rm_error)
        except Exception as e:
            print(f"DeleteFailed: {item_path}, Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clear_folder.py <folder_path>")
        sys.exit(1)

    target_folder = sys.argv[1]
    clear_folder(target_folder)
