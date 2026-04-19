import csv

INPUT_FILE = "../dataset/clean_dataset.csv"
OUTPUT_FILE = "../dataset/clean_dataset_fixed.csv"

with open(INPUT_FILE, "r") as inp, open(OUTPUT_FILE, "w", newline="") as out:
    reader = csv.reader(inp)
    writer = csv.writer(out)

    header = next(reader)
    writer.writerow(header)

    for row in reader:
        if row[1] in ["lexical", "syntax", "semantic"]:
            writer.writerow(row)

print("Fixed dataset created.")
