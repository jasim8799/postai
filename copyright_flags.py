import json
import os
from datetime import datetime

FLAGS_JSON = "copyright_flags.json"

def load_flags():
    if not os.path.exists(FLAGS_JSON):
        return {}
    with open(FLAGS_JSON, "r") as f:
        return json.load(f)

def save_flags(flags_data):
    with open(FLAGS_JSON, "w") as f:
        json.dump(flags_data, f, indent=4)

def update_flag(shortcode, data):
    flags_data = load_flags()
    flags_data[shortcode] = data
    save_flags(flags_data)
    print(f"✅ Updated copyright_flags.json for {shortcode}")

def ensure_flags_file():
    if not os.path.exists(FLAGS_JSON):
        with open(FLAGS_JSON, "w") as f:
            json.dump({}, f, indent=4)
        print("✅ Created empty copyright_flags.json")
    else:
        print("✅ copyright_flags.json already exists")
