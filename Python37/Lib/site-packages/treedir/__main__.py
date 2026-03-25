import argparse

from treedir.tree import tree_dir


def main(*args, **kwargs):
    parser = argparse.ArgumentParser(description="仿Linux树形目录显示，含文件/文件夹大小统计")
    parser.add_argument('-p', '--path', help="进行递归显示的目录路径，默认为当前目录", default=".")
    parser.add_argument('-m', '--max-level', type=int, help="递归展示的最大层数,默认为7层", default=7)
    parser.add_argument('-n', '--no-calc', action='store_true', help="指定该参数后，对于超过递归显示的最大层数的文件夹不再继续递归计算文件夹大小")
    args = parser.parse_args()

    tree_dir(args.path, args.max_level, args.no_calc)


if __name__ == "__main__":
    main()
