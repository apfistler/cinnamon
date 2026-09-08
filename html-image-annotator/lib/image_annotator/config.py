import os
import yaml


def load_config(filename):
  with open(filename, "r") as f:
    return yaml.safe_load(f) or {}

