import os

import Merge001ToRelease

if __name__ == '__main__':
    file_path = r'D:\AssetMergeTool\PathToReleaseFrom001.txt'
    Merge001ToRelease.run_release_pipeline_list(file_path, "001 To release List:" + file_path)
    