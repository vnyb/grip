import datetime
import io
import dateutil.parser
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

def read_last_line(fp: io.BufferedReader, ignore_empty_lines=False) -> str | None:
    fp.seek(0, 2)  # Move to the end of the file
    pos = start = end = fp.tell()

    def read() -> bytes | None:
        nonlocal pos

        pos -= 1
        fp.seek(pos)
        return fp.read(1)

    while pos > 0:
        char = read()

        if char == b'\n':
            if end - start == 0 and ignore_empty_lines:
                end = start = pos
                continue
            break
        else:
            start = pos

    n = end - start
    if n <= 0:
        return None if ignore_empty_lines else ""

    fp.seek(start)
    return fp.read(n).decode()

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

def now() -> datetime.datetime:
    return datetime.datetime.now().astimezone()

def date_to_str(date: datetime.date | datetime.datetime) -> str:
    return date.strftime("%Y-%m-%d")

def parse_iso_date(string: str) -> datetime.date:
    if len(string) == 7:
        string = string + "-01"
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()

def parse_iso_datetime(string: str) -> datetime.datetime:
    if len(string) == 7:
        string = string + "-01"
    return dateutil.parser.isoparse(string).astimezone()

def deep_dict_equal(a: dict, b: dict) -> bool:
    for key in a.keys():
        if key not in b:
            return False
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            if not deep_dict_equal(a[key], b[key]):
                return False
        if a[key] != b[key]:
            return False

    for key in b.keys():
        if key not in a:
            return False

    return True
