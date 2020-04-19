import json


def save_as_json(obj: object, path: str):
    with open(path, "w") as file:
        json.dump(obj, file, indent=2)
