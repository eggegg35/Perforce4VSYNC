"""
小小明的代码
CSDN主页：https://blog.csdn.net/as604049322
"""

import difflib
import os
import platform

import cchardet


def file_diff_compare(file1, file2, diff_out="diff_result.html", max_width=70, numlines=0, show_all=False,
                      no_browser=True):
    with open(file1, "rb") as f:
        bytes: bytes = f.read()
        text1 = bytes.decode(cchardet.detect(bytes)['encoding'])
        text1 = text1.splitlines(keepends=True)
    with open(file2, "rb") as f:
        bytes: bytes = f.read()
        text2 = bytes.decode(cchardet.detect(bytes)['encoding'])
        text2 = text2.splitlines(keepends=True)

    d = difflib.HtmlDiff(wrapcolumn=max_width)
    with open(diff_out, 'w', encoding="u8") as f:
        f.write(d.make_file(text1, text2, context=not show_all, numlines=numlines))
    abspath = os.path.abspath(diff_out).replace("\\", "/")
    out_uri = f"file:///{abspath}"
    print("输出到：", out_uri)
    if not no_browser:
        platform_system = platform.system()
        if platform_system == "Windows":
            os.system(f"cmd /c start {out_uri}")
        elif platform_system == "Linux":
            os.system(f"x-www-browser '{out_uri}'")
        else:
            os.system(f"open '{out_uri}'")
