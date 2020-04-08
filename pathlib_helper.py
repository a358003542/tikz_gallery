import os
import re
import logging


def gen_filetree(startpath='.', filetype=""):
    """
    利用os.walk 遍历某个目录，收集其内的文件，返回
    (文件路径列表, 本路径下的文件列表)
    比如:
    (['shortly'], ['shortly.py'])
(['shortly', 'templates'], ['shortly.py'])
(['shortly', 'static'], ['shortly.py'])

    第一个可选参数 startpath  默认值 '.'
    第二个参数  filetype  正则表达式模板 默认值是"" 其作用是只选择某些文件
    如果是空值，则所有的文件都将被选中。比如 "html$|pdf$" 将只选中 html和pdf文件。
    """
    for root, dirs, files in os.walk(startpath):
        filelist = []
        for f in files:
            fileName, fileExt = os.path.splitext(f)
            if filetype:
                if re.search(filetype, fileExt):
                    filelist.append(f)
            else:
                filelist = files
        if filelist:  # 空文件夹不加入
            dirlist = root.split(os.path.sep)
            dirlist = dirlist[1:]
            if dirlist:
                yield (dirlist, filelist)
            else:
                yield (['.'], filelist)


def gen_allfile(startpath='.', filetype=""):
    """
    利用os.walk 遍历某个目录，收集其内的文件，返回符合条件的文件路径名
    是一个生成器。
    第一个可选参数 startpath  默认值 '.'
    第二个参数  filetype  正则表达式模板 默认值是"" 其作用是只选择某些文件
    如果是空值，则所有的文件都将被选中。比如 "html$|pdf$" 将只选中 html和pdf文件。
    """

    for dirlist, filelist in gen_filetree(startpath=startpath,
                                          filetype=filetype):
        for f in filelist:
            filename = os.path.join(os.path.join(*dirlist), f)
            yield filename