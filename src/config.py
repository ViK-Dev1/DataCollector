import json
from pathlib import Path

'''
Loads the config.json file and make it available as a dictionary in the application
'''
def _load() -> dict:
    path = Path(__file__).parent / "config.json"
    with open(path, "r") as f:
        return json.load(f)


cfg: dict = _load()
