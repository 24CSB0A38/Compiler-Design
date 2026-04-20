import pandas as pd
import subprocess
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

# Paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(_SCRIPT_DIR, "..", "dataset", "CLACER_repo", "CLACER-main", "DataSet", "DataSet.csv")
output_path = os.path.join(_SCRIPT_DIR, "..", "dataset", "clacer_dataset.csv")
gcc_path = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "mingw64", "bin", "gcc.exe"))

if not os.path.exists(gcc_path):
    gcc_path = "gcc"

label_map = {
    0: "semantic",
    1: "syntax",
    2: "lexical",
    3: "semantic",
    4: "syntax",
    5: "semantic",
}

def process_single_row(index, code, class_id):
    # Clean the line numbers from the CLACER code format
    cleaned_code = []
    for line in str(code).split('\n'):
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[0].isdigit():
            cleaned_code.append(parts[1])
        else:
            cleaned_code.append(line)
            
    temp_c = f"temp_worker_{index}.c"
    with open(temp_c, "w") as f:
        f.write("\n".join(cleaned_code))
        
    try:
        result = subprocess.run([gcc_path, "-fmax-errors=1", temp_c], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        err = result.stderr.strip()
    except Exception:
        err = ""
    finally:
        if os.path.exists(temp_c):
            os.remove(temp_c)
            
    # Extract the main error line
    main_error = ""
    for eline in err.split("\n"):
        if "error:" in eline:
            main_error = eline.split("error:")[-1].strip()
            break
            
    if main_error:
        label = label_map.get(class_id, "semantic")
        return {"compiler": "gcc", "error_message": "error: " + main_error, "label": label}
    return None

def main():
    if not os.path.exists(csv_path):
        print(f"❌ Dataset not found at {csv_path}")
        return

    print("Loading CLACER DataSet.csv...")
    df = pd.read_csv(csv_path, nrows=10000)
    
    print(f"Compiling {len(df)} codes using multi-processing pool. This will be MUCH faster...")
    
    results = []
    # Use multiple CPU cores to speed up compilation
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(process_single_row, i, row['code'], row['error_class_id']): i 
                   for i, row in df.iterrows()}
        
        count = 0
        for future in as_completed(futures):
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as e:
                # Catch failures in individual rows but keep the script running
                pass
            
            count += 1
            if count % 100 == 0:
                print(f"Progress: {count}/{len(df)} processed (Found {len(results)} valid errors)...")

    if results:
        out_df = pd.DataFrame(results)
        out_df.to_csv(output_path, index=False)
        print(f"\n✅ SUCCESS! Extracted {len(out_df)} authentic GCC errors into {output_path}")
    else:
        print("\n❌ Failed to extract any valid errors.")

if __name__ == "__main__":
    main()
