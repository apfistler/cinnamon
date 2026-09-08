import os

def find_images(document):
  return document.find_all("img")


def get_image_src(image):
  return image.get("src")

def resolve_image_path(config, src):
  return os.path.join(
    config["paths"]["webroot"],
    src.lstrip("/")
  )


def image_exists(path):
  return os.path.isfile(path)


def image_size(path):
  return os.path.getsize(path)
