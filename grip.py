import logging
import os
import sys
import yaml

from typing import NoReturn

def die(message) -> NoReturn:
    logging.error(message)
    sys.exit(1)

def require_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        die(f"environment variable '{name}' is not set")
        
def read_yaml(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def save_yaml(data, path: str):
    with open(path, "w", encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)

def yaml_str_representer(dumper, data):
    if '\n' in data:  # Si la chaîne contient plusieurs lignes
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, yaml_str_representer)
