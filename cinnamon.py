#!/usr/bin/env python3

import os
import argparse

from lib.template import Template
from lib.output import Output
from lib.parser import Parser


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML from a Cinnamon page directory'
    )

    parser.add_argument(
        'input_dir',
        type=str,
        help='Input page directory'
    )

    parser.add_argument(
        '--template_filename',
        type=str,
        default='./templates/template.html',
        help='Template file name'
    )

    parser.add_argument(
        '--config_filename',
        type=str,
        default='./etc/config.yaml',
        help='Configuration file name'
    )

    parser.add_argument(
        '--output_dir',
        type=str,
        default='./output',
        help='Output directory path'
    )

    args = parser.parse_args()

    # Normalize the input directory
    input_dir = os.path.normpath(args.input_dir)

    # Make sure the input is inside the input directory
    input_root = os.path.abspath('input')
    input_path = os.path.abspath(input_dir)

    if not (
        input_path == input_root
        or input_path.startswith(input_root + os.sep)
    ):
        parser.error(
            'input directory must be inside input/'
        )

    if not os.path.isdir(input_dir):
        parser.error(
            f'input directory does not exist: {input_dir}'
        )

    # Page name is the directory name
    page_name = os.path.basename(input_dir)

    # The page HTML file is <page_dir>/<page_name>.html
    input_filename = os.path.join(
        input_dir,
        f'{page_name}.html'
    )

    if not os.path.isfile(input_filename):
        parser.error(
            f'input file does not exist: {input_filename}'
        )

    # Preserve the directory structure beneath input/
    #
    # input/html/main/home/
    #        ↓
    # output/html/main/home.html
    relative_dir = os.path.relpath(
        input_dir,
        input_root
    )

    output_filename = os.path.join(
        args.output_dir,
        f'{relative_dir}.html'
    )

    # Make sure the output directory exists
    os.makedirs(
        os.path.dirname(output_filename),
        exist_ok=True
    )

    template_obj = Template(
        args.template_filename
    )

    output_obj = Output(
        output_filename
    )

    parser_obj = Parser(
        input_dir,
        template_obj,
        args.config_filename,
        output_obj
    )

    parser_obj.parse_template()


if __name__ == '__main__':
    main()
