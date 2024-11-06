import re
from unidecode import unidecode
import yaml


def clean_text(text: str) -> str:
    text_lower = text.lower()
    text_no_punctuation = re.sub(r'[^\w\s]', '', text_lower)
    text_no_apostrophe = text_no_punctuation.replace("'", "")
    text_no_accent = unidecode(text_no_apostrophe)
    text_parts = text_no_accent.split(' ')
    output = ' '.join([x for x in text_parts if x])
    return output

def read_text(path: str) -> str:
    with open(path, 'r') as file:
        output = file.read().rstrip()
    return output


def read_yaml(path: str) -> dict:
    with open(path, 'r') as yaml_stream:
        output = yaml.safe_load(yaml_stream)
    return output


def write_yaml(item: dict, path: str) -> None:
    with open(path, 'w') as yaml_file:
        yaml.dump(item, yaml_file)
