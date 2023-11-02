from bs4 import BeautifulSoup

class Output:
    def __init__(self, filename):
        self.filename = filename

    def write(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        formatted_html = self._prettify_with_indentation(soup, indent=2)
        with open(self.filename, 'w') as output_file:
            output_file.write(formatted_html)

    def _prettify_with_indentation(self, soup, indent):
        pretty_html = soup.prettify()
        lines = pretty_html.split("\n")
        indented_html = ""
        for line in lines:
            indented_html += " " * indent + line + "\n"
        return indented_html

