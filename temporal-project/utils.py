import json
from typing import Any
import os


def save_json(file_path: str, data_item):
    with open(file_path, "w") as f:
        json.dump(data_item, f, indent=2)

def read_json(file_path: str) -> Any:
    with open(file_path, "r") as f:
        return json.load(f)
    
def remove_file(file_path: str):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)

