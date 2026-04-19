import pandas as pd
import subprocess
import os

# Paths
csv_path = "../dataset/CLACER_repo/CLACER-main/DataSet/DataSet.csv"
output_path = "../dataset/clacer_dataset.csv"

# CLACER class mappings (General approximation based on their paper)
# 0 = Semantic (Undeclared, Type Mismatch)
# 1 = Syntax (Missing bracing, boundaries)
# 2 = Lexical (Missing includes, bad syntax)
# 3 = Semantic (Out of bounds)
# 4 = Syntax
# 5 = Semantic
label_map = {
    0: "semantic",
    1: "syntax",
    2: "lexical",
    3: "semantic",
    4: "syntax",
    5: "semantic",
}

print("Loading CLACER DataSet.csv...")
# We will process 1000 codes to extract their GCC actual error strings
df = pd.read_csv(csv_path, nrows=1000)

output_rows = []
temp_c = "temp_clacer.c"

print(f"Compiling {len(df)} CLACER codes with GCC to extract raw error messages. This will take roughly 10-20 seconds...")

for index, row in df.iterrows():
    code = row['code']
    
    # Clean the line numbers from the CLACER code format (e.g. "  1 #include")
    cleaned_code = []
    for line in str(code).split('\n'):
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[0].isdigit():
            cleaned_code.append(parts[1])
        else:
            cleaned_code.append(line)
            
    with open(temp_c, "w") as f:
        f.write("\n".join(cleaned_code))
        
    result = subprocess.run(["gcc", "-fmax-errors=1", temp_c], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err = result.stderr.strip()
    
    # Extract the main error line
    main_error = ""
    for eline in err.split("\n"):
        if "error:" in eline:
            main_error = eline.split("error:")[-1].strip()
            break
            
    if main_error:
        class_id = row['error_class_id']
        label = label_map.get(class_id, "semantic") # Default to semantic if unknown
        output_rows.append({"compiler": "gcc", "error_message": "error: " + main_error, "label": label})

if os.path.exists(temp_c):
    os.remove(temp_c)

out_df = pd.DataFrame(output_rows)
out_df.to_csv(output_path, index=False)
print(f"\n✅ Success! Extracted {len(out_df)} completely authentic GCC errors into {output_path}")
