import argparse

from filediff.diff import file_diff_compare


def main(*args, **kwargs):
    parser = argparse.ArgumentParser(description="比较两个文本文件的差异输出到HTML网页中")
    parser.add_argument('file1', help='被比较的文件1')
    parser.add_argument('file2', help='被比较的文件2')
    parser.add_argument('-o', '--out', help='差异结果保存的文件名，默认值diff_result.html', default="diff_result.html")
    parser.add_argument('-m', '--max_width', type=int, help='每行超过多少字符就自动换行，默认值70', default=70)
    parser.add_argument('-n', '--numlines', type=int, help='在差异行基础上前后显示多少行，默认是0', default=0)
    parser.add_argument('-a', '--show_all', help='只要设置这个参数就表示显示全部原始数据，此时-n参数无效；默认不显示全部',
                        action='store_true', default=False)
    parser.add_argument('--no-browser', help='设置这个参数，在生成结果后不会自动打开游览器',
                        action='store_true', default=False)
    args = parser.parse_args()
    file_diff_compare(args.file1, args.file2, args.out, args.max_width, args.numlines, args.show_all, args.no_browser)


if __name__ == "__main__":
    main()
