import os
import sys
import yaml

CONFIG_DIR = os.path.dirname(__file__)

def load_yaml(filename):
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.isfile(path):
        print(f"ERROR: {filename} not found in config/")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)

def load_config():
    return load_yaml("config.yaml")

def load_stream_config():
    return load_yaml("stream.yaml")

def load_hpl_config():
    return load_yaml("hpl.yaml")
