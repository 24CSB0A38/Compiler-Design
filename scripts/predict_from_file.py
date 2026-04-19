import subprocess
import pickle
import sys
import os
import re

# -------------------------------
# Load trained model
# -------------------------------
with open("../compiler_error_model.pkl", "rb") as f:
    model, vectorizer = pickle.load(f)

# -------------------------------
# Validate arguments
# -------------------------------
if len(sys.argv) != 2:
    print("Usage: python predict_from_file.py <path_to_c_file>")
    sys.exit(1)

c_file = sys.argv[1]

if not os.path.exists(c_file):
    print("Error: File not found.")
    sys.exit(1)

# -------------------------------
# Compile file
# -------------------------------
result = subprocess.run(
    ["gcc", "-fmax-errors=100", c_file],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

if not result.stderr.strip():
    print("No compilation errors found.")
    sys.exit(0)

# -------------------------------
# Extract all error lines
# -------------------------------
error_lines = result.stderr.strip().split("\n")
all_errors = []

for line in error_lines:
    if "error:" in line.lower():
        all_errors.append(line)

if not all_errors and error_lines and error_lines[0]:
    all_errors = [error_lines[0]]  # Fallback if no explicit "error:" found

# -------------------------------
# Output Header
# -------------------------------
print("\n" + "=" * 60)
print("      COMPILER ERROR CLASSIFICATION SYSTEM")
print("=" * 60)
print(f"\nInput File: {c_file}")
print(f"Total Errors Detected: {len(all_errors)}")

# -------------------------------
# Predict & Output for each error
# -------------------------------
for i, raw_error in enumerate(all_errors, 1):
    # Clean file paths and line numbers
    clean_error = re.sub(r".*?:\d+:\d+:\s*", "", raw_error)
    error_message = clean_error.strip()
    error_lower = error_message.lower()

    # Hybrid Rule + ML Prediction
    if "undeclared" in error_lower:
        prediction = "semantic"
        reason = "Rule-based: 'undeclared' keyword detected."
    elif "expected" in error_lower:
        prediction = "syntax"
        reason = "Rule-based: 'expected' keyword detected."
    elif "invalid" in error_lower or "token" in error_lower:
        prediction = "lexical"
        reason = "Rule-based: invalid token pattern detected."
    else:
        vec = vectorizer.transform([error_message])
        prediction = model.predict(vec)[0]
        reason = "Predicted using trained ML model."

    # -------------------------------
    # Security Risk Analyzer (Semantic)
    # -------------------------------
    security_risk = None
    cwe_id = None
    severity = None
    
    if prediction == "semantic":
        # Check for common memory and security vulnerability patterns
        if "dereferencing pointer" in error_lower or "null pointer" in error_lower or ("pointer" in error_lower and "type" in error_lower):
            security_risk = "NULL Pointer Dereference / Invalid Memory Access"
            cwe_id = "CWE-476"
            severity = "🔴 HIGH"
        elif "array subscript" in error_lower or "bounds" in error_lower or "overflow" in error_lower:
            security_risk = "Out-of-Bounds Memory Buffer / Buffer Overflow"
            cwe_id = "CWE-119"
            severity = "🔴 HIGH"
        elif "format" in error_lower and ("string" in error_lower or "literal" in error_lower):
            security_risk = "Externally-Controlled Format String"
            cwe_id = "CWE-134"
            severity = "🟠 MEDIUM"
        elif "free" in error_lower or "unallocated" in error_lower:
            security_risk = "Use After Free / Double Free Vulnerability"
            cwe_id = "CWE-416 / CWE-415"
            severity = "🔴 CRITICAL"
        elif "address" in error_lower and "local" in error_lower:
            security_risk = "Return of Stack Variable Address"
            cwe_id = "CWE-562"
            severity = "🟠 MEDIUM"
        else:
            security_risk = "General Logic Flaw (Potential Security Implication)"
            cwe_id = "CWE-699"
            severity = "🟡 LOW"

    print(f"\n--- Error {i} ---")
    print("Detected Compiler Error:", error_message)
    print("Predicted Error Type:", prediction.upper())
    
    if security_risk:
        print("\n   [!] MINOR TO CRITICAL SECURITY VULNERABILITY ALERT [!]")
        print(f"   Severity:      {severity}")
        print(f"   Vulnerability: {security_risk}")
        print(f"   CWE Standard:  {cwe_id}")
        print("   " + "-"*48)
        
    print("Decision Source:", reason)

print("\n" + "=" * 60)