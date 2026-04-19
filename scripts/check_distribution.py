import csv
from collections import Counter

with open("../dataset/clean_dataset_fixed.csv") as f:
    reader = csv.reader(f)
    next(reader)

    labels = [row[1] for row in reader]

print("Label distribution:")
print(Counter(labels))
