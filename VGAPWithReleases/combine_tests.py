import os
import sys
import json
from pathlib import Path
from collections import defaultdict

def sum_json_files_in_dir(directory):
    total = defaultdict(float)

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
        with open(filepath) as f:
            data = json.load(f)
            for key, value in data.items():
                total[key] += value


    # Convert defaultdict back to normal dict
    total = dict(total)

    with open(Path(directory) / "total", "w") as f:
        json.dump(total, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <directory> [output_file]")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    sum_json_files_in_dir(directory)
