import subprocess
import csv
import sys
import os

DATASET_FILE = "../dataset/labeled_dataset.csv"

def compile_c_file(c_file):
    result = subprocess.run(
        ["gcc", c_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stderr.strip()

def save_error(error_msg, label):
    with open(DATASET_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["gcc", error_msg, label])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_compiler.py <c_file> <label>")
        sys.exit(1)

    c_file = sys.argv[1]
    label = sys.argv[2]

    if not os.path.exists(c_file):
        print("File not found")
        sys.exit(1)

    error = compile_c_file(c_file)

    if error:
        save_error(error, label)
        print("Error captured and saved")
    else:
        print("No compilation error")