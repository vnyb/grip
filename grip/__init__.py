import datetime
import json
import logging
import os
import sys
import yaml

from typing import NoReturn

def remove_suffix(string: str, suffix: str) -> str:
    if string.endswith(suffix):
        return string[:-len(suffix)]
    return string

def die(message: str) -> NoReturn:
    logging.error(message)
    sys.exit(1)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def require_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        die(f"environment variable '{name}' is not set")

def get_file_age(path: str) -> datetime.timedelta:
    timestamp = os.path.getctime(path)
    creation_date = datetime.datetime.fromtimestamp(timestamp)
    return datetime.datetime.now() - creation_date

def get_file_staleness(path: str) -> datetime.timedelta:
    timestamp = os.path.getmtime(path)
    last_modified_date = datetime.datetime.fromtimestamp(timestamp)
    return datetime.datetime.now() - last_modified_date

def read_file(path: str) -> str:
    with open(path, 'r') as file:
        return file.read()

def write_file(data, path: str):
    with open(path, 'w') as file:
        return file.write(data)

def read_json(path: str):
    with open(path, 'r') as file:
        return json.load(file)

def write_json(data, path: str, indent=True):
    with open(path, 'w') as file:
        return json.dump(data, file, indent=indent)

        
def read_yaml(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def save_yaml(data, path: str):
    with open(path, "w", encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True, sort_keys=False)

def yaml_str_representer(dumper, data):
    if '\n' in data:  # Si la chaîne contient plusieurs lignes
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, yaml_str_representer)
