import subprocess
import csv
import os

DATASET_FILE = "../dataset/labeled_dataset.csv"
BASE_DIR = "../error_programs"

with open(DATASET_FILE, "a", newline="") as f:
    writer = csv.writer(f)

    for label in ["lexical", "syntax", "semantic"]:
        folder = os.path.join(BASE_DIR, label)

        for file in os.listdir(folder):
            if file.endswith(".c"):
                path = os.path.join(folder, file)

                result = subprocess.run(
                    ["gcc", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if result.stderr:
                    writer.writerow(["gcc", result.stderr.strip(), label])

print("All compiler errors collected successfully.")