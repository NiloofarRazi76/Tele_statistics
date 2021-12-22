import json

def read_json(file_path: str) -> dict:
    """Read a json file and returns the dict
    """

    with open(file_path) as f:
        return json.load(f)

def read_file(file_path: str) -> str:
    """Read a file and return the content
    """

    with open(file_path) as f:
        return f.read()
