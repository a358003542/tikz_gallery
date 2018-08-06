#!/usr/bin/env python
# -*-coding:utf-8-*-


"""
1. scan gallery folder
2. convert the pdf -> png
3. get png link and get code link
4. generate markdown

"""
import os

from jinja2 import Template

from bihu.utils.path_utils import gen_allfile
from ximage.convert.convert_image import convert_image


FOLDER_NAME = 'gallery'
MARKDOWN_NAME = 'GALLERY.md'

def scan_folder():
    g = gen_allfile(FOLDER_NAME, '\.tex$')
    all_files = [os.path.join(FOLDER_NAME, filename) for filename in g]
    return all_files


def convert_pdf_to_png(all_files):
    for filename in all_files:
        filename = filename[:-4] + '.pdf'
        convert_image(filename)


def create_link_data(all_files):
    link_data = []

    for filename in all_files:
        item = {}
        item['name'] = os.path.splitext(filename)[0][len(FOLDER_NAME)+1:]

        filename_url = filename.replace('\\', '/')
        item['tex'] = filename_url
        item['png'] = filename_url[:-4] + '.png'

        link_data.append(item)

    return link_data


def generate_markdown(link_data):
    template_content = open('GALLERY.jinja2', 'rt').read()

    with open(MARKDOWN_NAME, 'wt') as f:
        template = Template(template_content)
        content = template.render(link_data=link_data)

        f.write(content)


def main():
    all_files = scan_folder()

    convert_pdf_to_png(all_files)

    link_data = create_link_data(all_files)

    generate_markdown(link_data)


if __name__ == '__main__':
    main()