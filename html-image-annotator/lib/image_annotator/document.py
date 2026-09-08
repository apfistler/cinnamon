from bs4 import BeautifulSoup


def load_document(filename):
  with open(filename, "r", encoding="utf-8") as f:
    return BeautifulSoup(f, "html.parser")
