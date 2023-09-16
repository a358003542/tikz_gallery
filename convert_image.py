#!/usr/bin/env python
# -*-coding:utf-8-*-

import sys
import logging
import os.path
import subprocess
import shutil
import click
from PIL import Image

import os
import errno
import os.path


logger = logging.getLogger(__name__)


def mkdirs(path, mode=0o777):
    """
    Recursive directory creation function base on os.makedirs with a little error handling.
    """
    try:
        os.makedirs(path, mode=mode)
    except OSError as e:
        if e.errno != errno.EEXIST:  # File exists
            logger.error('file exists: {0}'.format(e))
            raise IOError


def detect_output_file_exist(basedir, imgname, outputformat, overwrite):
    filename = '{}.{}'.format(imgname, outputformat)
    filename = os.path.join(basedir, filename)

    if os.path.exists(filename) and not overwrite:
        click.echo('output image file exists. i will give it up.')
        return None
    return filename


def convert_encoding(origin_s, origin_encoding, to_encoding,
                     errors='ignore'):
    b = origin_s.encode(origin_encoding, errors=errors)
    s = b.decode(to_encoding, errors)
    return s


class ConfigFileNotFoundError(FileNotFoundError):
    """
    配置文件没有找到
    """


class RequireArgumentError(Exception):
    """
    需要某个参数但是没有提供
    """


class CommandNotFound(Exception):
    """
    system doesnot have that command
    """


class PillowProcessError(Exception):
    pass


class InkscapeProcessError(Exception):
    pass


class PdftocairoProcessError(Exception):
    pass


logger = logging.getLogger(__name__)

pillow_support = ['png', 'jpg', 'jpeg', 'gif', 'tiff', 'bmp', 'ppm']


def convert_image_by_pillow(inputimg, outputdir, output_imgname, outputname='',
                            outputformat='png', overwrite=True,
                            dpi=150):
    """

    """
    outputimg = detect_output_file_exist(outputdir, output_imgname,
                                         outputformat,
                                         overwrite)
    if not outputimg:
        return None

    if inputimg == outputimg:
        raise FileExistsError

    try:
        img = Image.open(inputimg)
        img.save(outputimg)
        logger.info('{0} saved.'.format(outputimg))
        return outputimg
    except FileNotFoundError as e:
        raise PillowProcessError(
            f"process image: {inputimg} raise FileNotFoundError")
    except IOError:
        raise PillowProcessError(f"process image: {inputimg} raise IOError")


def convert_image_by_inkscape(inputimg, outputdir, output_imgname,
                              outputname='', outputformat='png', overwrite=True,
                              dpi=150):
    outputimg = detect_output_file_exist(outputdir, output_imgname,
                                         outputformat,
                                         overwrite)
    if not outputimg:
        return None

    if inputimg == outputimg:
        raise FileExistsError

    if outputformat == 'png':
        outflag = 'e'
    elif outputformat == 'pdf':
        outflag = 'A'
    elif outputformat == 'ps':
        outflag = 'P'
    elif outputformat == 'eps':
        outflag = 'E'

    if shutil.which('inkscape'):
        process_cmd = ['inkscape', '-zC',
                       '-f', inputimg, '-{0}'.format(outflag),
                       outputimg, '-d', str(dpi)]
        logger.debug(f'start call cmd {process_cmd}')
        subprocess.check_call(process_cmd)
        return outputimg  # only retcode is zero
    else:
        raise InkscapeProcessError("inkscape commond not found.")


def fix_filename_encoding_problem(output_imgname, outputformat, overwrite=True,
                                  pdftocairo_fix_encoding=''):
    if 'win32' == sys.platform.lower():
        if pdftocairo_fix_encoding:
            output_imgname2 = convert_encoding(output_imgname,
                                               'utf8',
                                               pdftocairo_fix_encoding)

            if overwrite:
                os.replace('{}.{}'.format(output_imgname2,
                                          outputformat),
                           '{}.{}'.format(output_imgname,
                                          outputformat))
            else:
                try:
                    os.rename('{}.{}'.format(output_imgname2,
                                             outputformat),
                              '{}.{}'.format(output_imgname,
                                             outputformat))
                except FileExistsError as e:
                    logger.info(
                        'FileExists , i will do nothing.')
                    os.remove('{}.{}'.format(output_imgname2,
                                             outputformat))


def convert_image_by_pdftocairo(inputimg, outputdir, output_imgname,
                                outputname='', outputformat='png',
                                overwrite=True,
                                dpi=150, pdftocairo_fix_encoding='',
                                transparent=False):
    outputimg = detect_output_file_exist(outputdir, output_imgname,
                                         outputformat,
                                         overwrite)
    if not outputimg:
        return None

    if not shutil.which('pdftocairo'):
        raise PdftocairoProcessError("pdftocairo commond not found.")

    currdir = os.path.abspath(os.curdir)
    os.chdir(outputdir)
    map_dict = {i: '-{}'.format(i) for i in
                ['png', 'pdf', 'ps', 'eps', 'jpeg', 'svg']}

    outflag = map_dict[outputformat]

    try:
        if outputformat in ['png', 'jpeg']:
            # png jpeg without ext so use the output_imgname
            process_cmd = ['pdftocairo', outflag, '-singlefile', '-r', str(dpi),
                           inputimg, output_imgname]

            if transparent and outputformat == 'png':
                process_cmd.insert(2, '-transp')

            logger.debug(f'start call cmd {process_cmd}')
            subprocess.check_call(process_cmd)

            fix_filename_encoding_problem(output_imgname,
                                          outputformat,
                                          overwrite=overwrite,
                                          pdftocairo_fix_encoding=pdftocairo_fix_encoding)
        else:
            process_cmd = ['pdftocairo', outflag, '-r', str(dpi), inputimg,
                           outputname]
            if transparent and outputformat == 'tiff':
                process_cmd.insert(2, '-transp')

            logger.debug(f'start call cmd {process_cmd}')
            subprocess.check_call(process_cmd)
        return outputimg  # only retcode is zero
    finally:
        os.chdir(currdir)


def convert_image(inputimg, outputformat='png', dpi=150, outputdir='',
                  outputname='', pdftocairo_fix_encoding='',
                  overwrite=True, transparent=False):
    """
    - intputimg 输入图片
    - outputformat
    - dpi 输出图片dpi
    - overwrite 图片是否覆写
    - outputname 输出图片名 带后缀
    - output_imgname 输出图片名 不带后缀
    本函数若图片转换成功则返回目标目标在系统中的路径，否则返回None。
    文件basedir路径默认和inputimg相同，若有更进一步的需求，则考虑
    """
    inputimg = os.path.abspath(inputimg)

    outputdir = os.path.abspath(outputdir)
    if not os.path.exists(outputdir):
        mkdirs(outputdir)

    imgname, imgext = os.path.splitext(os.path.basename(inputimg))

    if not outputname:
        outputname = imgname + '.{}'.format(outputformat)
        output_imgname = imgname
    else:
        output_imgname, ext = os.path.splitext(outputname)
        if not ext:
            outputname = output_imgname + '.{}'.format(outputformat)
        elif ext != outputformat:
            raise Exception(
                'outputname ext is not the same as the outputformat')

    try:
        if imgext[1:] in pillow_support and outputformat in pillow_support:
            return convert_image_by_pillow(inputimg, outputdir, output_imgname,
                                           outputname=outputname,
                                           outputformat=outputformat,
                                           dpi=dpi, overwrite=overwrite)
        elif imgext[1:] in ['svg', 'svgz'] and outputformat in ['png', 'pdf',
                                                                'ps',
                                                                'eps']:
            return convert_image_by_inkscape(inputimg, outputdir,
                                             output_imgname,
                                             outputname=outputname,
                                             outputformat=outputformat,
                                             dpi=dpi, overwrite=overwrite)

        elif imgext[1:] in ['pdf'] and outputformat in ['png', 'jpeg', 'ps',
                                                        'eps',
                                                        'svg']:
            return convert_image_by_pdftocairo(inputimg, outputdir,
                                               output_imgname,
                                               outputname=outputname,
                                               outputformat=outputformat,
                                               dpi=dpi,
                                               overwrite=overwrite,
                                               pdftocairo_fix_encoding=pdftocairo_fix_encoding,
                                               transparent=transparent)
    except PillowProcessError as e:
        logger.error(e)
    except InkscapeProcessError as e:
        logger.error(e)
    except PdftocairoProcessError as e:
        logger.error(e)
