from urllib.parse import urljoin

from bs4 import BeautifulSoup


class SubstackOutput:
  BASE_URL = 'https://www.adamfistler.com/'

  def __init__(self, source_filename, output_filename):
    self.source_filename = source_filename
    self.output_filename = output_filename

  def write(self):
    with open(self.source_filename, 'r') as input_file:
      content = input_file.read()

    soup = BeautifulSoup(
      content,
      'html.parser'
    )

    body = soup.body

    if body is None:
      raise ValueError(
        f'No <body> element found in '
        f"'{self.source_filename}'"
      )

    self._make_urls_absolute(body)

    output_html = self._extract_body(body)

    with open(self.output_filename, 'w') as output_file:
      output_file.write(output_html)

  def _make_urls_absolute(self, body):
    for tag in body.find_all(
      ['img', 'a', 'source', 'video', 'audio']
    ):

      if tag.name == 'a':
        attribute = 'href'
      else:
        attribute = 'src'

      value = tag.get(attribute)

      if not value:
        continue

      # Leave already-absolute URLs alone.
      if value.startswith(
        (
          'http://',
          'https://',
          '//',
          'data:',
          'mailto:',
          '#'
        )
      ):
        continue

      tag[attribute] = urljoin(
        self.BASE_URL,
        value
      )

  def _extract_body(self, body):
    return ''.join(
      str(element)
      for element in body.contents
    ).strip() + '\n'

