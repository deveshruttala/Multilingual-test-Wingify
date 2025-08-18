
import yaml
from pathlib import Path

def load_config(path: str = "config/config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Normalize paths
    root = Path(".")
    for key in ["urlsFile"]:
        if key in cfg and cfg[key]:
            cfg[key] = str(root / cfg[key])
    if "ignoredWordsFile" in cfg and cfg["ignoredWordsFile"]:
        cfg["ignoredWordsFile"] = str(root / cfg["ignoredWordsFile"])
    return cfg
