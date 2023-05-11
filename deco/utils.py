import pathlib

import yaml

APP_CONFIG = {}

def load_config(file: pathlib.Path) -> None:
    global APP_CONFIG
    
    if isinstance(file, str):
        file = pathlib.Path(file)
    
    APP_CONFIG = yaml.safe_load(file.read_text())

default_config_file = pathlib.Path('./config.yaml')

if default_config_file.exists():
    load_config(default_config_file)
