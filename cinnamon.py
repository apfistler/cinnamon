#!/usr/bin/env python3

import os
import argparse

from lib.template import Template
from lib.output import Output
from lib.parser import Parser
from lib.substack_output import SubstackOutput


def main():
  parser = argparse.ArgumentParser(
    description='Generate output from a Cinnamon page directory'
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

  parser.add_argument(
    '--output',
    action='append',
    choices=['html', 'substack'],
    default=None,
    help='Output format; may be specified multiple times'
  )

  args = parser.parse_args()

  # ---------------------------------------------------------------
  # Default output
  # ---------------------------------------------------------------
  #
  # Existing Cinnamon calls have always produced HTML.
  # Preserve that behavior unless --output is explicitly supplied.
  #
  output_types = args.output or ['html']

  # Remove duplicates while preserving the requested order.
  output_types = list(dict.fromkeys(output_types))

  # ---------------------------------------------------------------
  # Validate input directory
  # ---------------------------------------------------------------

  input_dir = os.path.normpath(args.input_dir)

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

  # ---------------------------------------------------------------
  # Determine page name and input file
  # ---------------------------------------------------------------

  page_name = os.path.basename(input_dir)

  input_filename = os.path.join(
    input_dir,
    f'{page_name}.html'
  )

  if not os.path.isfile(input_filename):
    parser.error(
      f'input file does not exist: {input_filename}'
    )

  # ---------------------------------------------------------------
  # Determine relative output path
  # ---------------------------------------------------------------

  relative_dir = os.path.relpath(
    input_dir,
    input_root
  )

  parts = os.path.normpath(relative_dir).split(os.sep)

  if parts and parts[0] == 'html':
    relative_dir = (
      os.path.join(*parts[1:])
      if len(parts) > 1
      else ''
    )

  # ---------------------------------------------------------------
  # Output paths
  # ---------------------------------------------------------------

  html_filename = os.path.join(
    args.output_dir,
    f'{relative_dir}.html'
  )

  substack_filename = os.path.join(
    args.output_dir,
    'substack',
    f'{relative_dir}.html'
  )

  # ---------------------------------------------------------------
  # Generate HTML
  # ---------------------------------------------------------------
  #
  # Substack output is derived from the completed HTML output.
  # Therefore, if Substack is requested without HTML explicitly,
  # HTML is still generated internally as the source for the
  # Substack transformation.
  #
  # ---------------------------------------------------------------

  if 'html' in output_types or 'substack' in output_types:

    html_directory = os.path.dirname(
      html_filename
    )

    os.makedirs(
      html_directory,
      exist_ok=True
    )

    template_obj = Template(
      args.template_filename
    )

    output_obj = Output(
      html_filename
    )

    parser_obj = Parser(
      input_dir,
      template_obj,
      args.config_filename,
      output_obj
    )

    parser_obj.parse_template()

  # ---------------------------------------------------------------
  # Generate Substack output
  # ---------------------------------------------------------------

  if 'substack' in output_types:

    substack_directory = os.path.dirname(
      substack_filename
    )

    os.makedirs(
      substack_directory,
      exist_ok=True
    )

    substack_output = SubstackOutput(
      html_filename,
      substack_filename
    )

    substack_output.write()


if __name__ == '__main__':
  main()

