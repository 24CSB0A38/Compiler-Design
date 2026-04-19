import csv
import re
import os

INPUT_FILE = "../dataset/labeled_dataset.csv"
OUTPUT_FILE = "../dataset/clean_dataset.csv"

write_header = not os.path.exists(OUTPUT_FILE)

def clean_error(msg):
    msg = re.sub(r".*?:\d+:\d+:", "", msg)
    msg = re.sub(r"\s+", " ", msg)
    return msg.strip()

with open(INPUT_FILE, "r") as inp, open(OUTPUT_FILE, "a", newline="") as out:
    reader = csv.reader(inp)
    writer = csv.writer(out)

    if write_header:
        writer.writerow(["error_message", "label"])

    for compiler, msg, label in reader:
        writer.writerow([clean_error(msg), label])

print("Clean dataset saved successfully.")
