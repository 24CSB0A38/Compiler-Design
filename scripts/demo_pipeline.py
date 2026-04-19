import sys
import os
import subprocess
import pickle
import json
import re

# Import standalone modules
from cwe_tagger import CWETagger
from readability_scorer import ReadabilityScorer
from profiler import CompilerFingerprintProfiler

MODEL_PATH = "../compiler_error_model.pkl"

if not os.path.exists(MODEL_PATH):
    print("Please run train_model.py first!")
    sys.exit(1)

with open(MODEL_PATH, "rb") as f:
    model, vectorizer = pickle.load(f)

# Module Initialization
cwe_tagger = CWETagger()
readability_scorer = ReadabilityScorer()
profiler = CompilerFingerprintProfiler()

def run_pipeline(c_file):
    print(f"\n[Phase 6] Running END-TO-END Explainable Pipeline on: {c_file}\n")
    
    # 1. Normalizer (Extract from GCC)
    result = subprocess.run(["gcc", "-fmax-errors=100", c_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    error_lines = result.stderr.strip().split("\n")
    
    all_errors = []
    for line in error_lines:
        if "error:" in line.lower():
            all_errors.append(line)

    if not all_errors and error_lines and error_lines[0]:
        all_errors = [error_lines[0]]
        
    print(f">> Normalizer caught {len(all_errors)} distinct compiler errors.\n")

    session_predictions = []
    pipeline_report = []

    # 2. Cascade Detector & Classifier
    for i, raw_error in enumerate(all_errors, 1):
        clean_error = re.sub(r".*?:\d+:\d+:\s*", "", raw_error).strip()
        
        # Classifier + Confidence Flag
        vec = vectorizer.transform([clean_error])
        prediction = model.predict(vec)[0]
        confidence = max(model.predict_proba(vec)[0])
        
        # Flag 'Ambiguous'
        ambiguous_flag = True if confidence < 0.65 else False
        
        # Readability Score
        readability = readability_scorer.generate_score(clean_error)
        
        # CWE Tagger JSON
        cwe_output = json.loads(cwe_tagger.tag_error(clean_error, prediction, confidence, cascade_group=f"Group_{i}"))
        
        # Append extra info
        cwe_output["ambiguous"] = ambiguous_flag
        cwe_output["readability_score"] = readability["readability_score_out_of_10"]
        cwe_output["has_hints"] = readability["contains_hints"]
        
        pipeline_report.append(cwe_output)
        session_predictions.append({"predicted_class": prediction})
        
    # 3. Fingerprint Profiler
    developer_profile = json.loads(profiler.profile_session(session_predictions))
    
    # 4. Generate Final Integrated System Build Report 
    final_output = {
        "Demonstration_Target": c_file,
        "Developer_Fingerprint": developer_profile,
        "Cascade_Error_Analysis": pipeline_report,
        "Summary": "Explainable end-to-end trace combining 7 uniquely engineered ML/logic modules"
    }
    
    print("="*60)
    print("  FINAL STRUCTURED OUTPUT REPORT  ")
    print("="*60)
    print(json.dumps(final_output, indent=4))
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python demo_pipeline.py <file.c>")
    else:
        run_pipeline(sys.argv[1])
