#!/usr/bin/python3

import os
import argparse
from lib.input_module.input import Input
from lib.output_module.output import Output
from lib.template_module.template import Template
from lib.parser_module.parser import Parser
from lib.metadata_module.metadata import Metadata  # Assuming the Metadata class is in a file named metadata.py

def main():
    parser = argparse.ArgumentParser(description='Generates HTML for Adam Fistler Website based on Template and Input File')
    parser.add_argument('input_filename', type=str, help='Input file name')
    parser.add_argument('--template_filename', type=str, default='./templates/template.html', help='Template file name')
    parser.add_argument('--config_filename', type=str, default='./etc/config.yaml', help='Configuration file name')
    parser.add_argument('--output_dir', type=str, default='./output', help='Output directory path')
    args = parser.parse_args()

    metadata_obj = Metadata(args.input_filename)
    input_obj = Input(args.input_filename, args.config_filename)
    template_obj = Template(args.template_filename)
    output_filename = metadata_obj.generate_output_filename(args.output_dir)
    output_obj = Output(output_filename)
    parser_obj = Parser(input_obj, template_obj, args.config_filename, output_obj, metadata_obj.metadata)
    parser_obj.parse_template()

if __name__ == '__main__':
    main()
