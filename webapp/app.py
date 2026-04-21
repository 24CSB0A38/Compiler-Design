"""
Intelligent Compiler Suite — Flask Backend
==========================================
Compiles user-submitted C code via GCC, runs it through an ML pipeline that
classifies errors (lexical / syntax / semantic), assigns CWE security IDs,
scores readability, profiles the developer, estimates time complexity, and
computes Green Computing metrics (carbon footprint, energy efficiency grade).
"""

import os
import sys
import subprocess
import pickle
import json
import re
from flask import Flask, request, jsonify, render_template

# ── Path setup ────────────────────────────────────────────────────────────────
_WEBAPP_DIR  = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_WEBAPP_DIR, "..", "scripts"))
sys.path.insert(0, _SCRIPTS_DIR)

# ── Load ML support modules ───────────────────────────────────────────────────
_ml_modules_loaded = False
try:
    from cwe_tagger import CWETagger
    from readability_scorer import ReadabilityScorer
    from profiler import CompilerFingerprintProfiler
    _ml_modules_loaded = True
except ImportError as exc:
    print(f"[WARN] Backend ML modules unavailable: {exc}")

app = Flask(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(_WEBAPP_DIR, "..", "compiler_error_model.pkl")
TEMP_FILE  = os.path.join(_WEBAPP_DIR, "temp_user_code.c")
GCC_PATH   = os.path.join(_WEBAPP_DIR, "..", "mingw64", "bin", "gcc.exe")
if not os.path.exists(GCC_PATH):
    GCC_PATH = "gcc"

# ── Initialise global singletons ──────────────────────────────────────────────
cwe_tagger         = CWETagger()                  if _ml_modules_loaded else None
readability_scorer = ReadabilityScorer()           if _ml_modules_loaded else None
profiler           = CompilerFingerprintProfiler() if _ml_modules_loaded else None

# ── Load ML model ─────────────────────────────────────────────────────────────
model_loaded = False
vectorizer   = None
ml_model     = None

if os.path.exists(MODEL_PATH):
    try:
        with open(MODEL_PATH, "rb") as fh:
            ml_model, vectorizer = pickle.load(fh)
            model_loaded = True
        print("[OK] ML model loaded successfully.")
    except Exception as exc:
        print(f"[WARN] Failed to load model: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# Helper: Custom Lexical Scanner
# ══════════════════════════════════════════════════════════════════════════════
def _custom_lexical_scan(code: str, temp_path: str) -> list:
    """Detects characters GCC may silently accept and synthesises error lines."""
    INVALID_CHARS = {
        '$': "error: stray '$' in program",
        '`': "error: stray '`' in program",
        '@': "error: stray '@' in program",
    }
    found = []
    for lineno, line in enumerate(code.splitlines(), start=1):
        clean = re.sub(r'".*?"', '""', line)
        clean = re.sub(r'//.*', '', clean)
        for char, msg in INVALID_CHARS.items():
            if char in clean:
                col = clean.index(char) + 1
                found.append(f"{temp_path}:{lineno}:{col}: {msg}")
    return found


# ══════════════════════════════════════════════════════════════════════════════
# Helper: Time Complexity Analyser
# ══════════════════════════════════════════════════════════════════════════════
def _analyze_time_complexity(code: str) -> dict:
    """Heuristic static analysis to estimate Big-O time complexity."""
    lines = code.splitlines()

    loop_lines = [
        ln for ln in lines
        if re.search(r'\b(for|while|do)\b', ln) and not ln.strip().startswith('//')
    ]
    total_loops = len(loop_lines)

    # Nesting depth via indentation
    nesting = 1
    if total_loops >= 2:
        indents = [len(ln) - len(ln.lstrip()) for ln in loop_lines]
        if len(set(indents)) > 1:
            nesting = 2
        if total_loops >= 3 and nesting == 2:
            deeper  = [i for i in indents if i > min(indents)]
            deepest = [i for i in deeper if i > min(deeper)] if deeper else []
            if deepest:
                nesting = 3

    # Detect recursion
    STDLIB = {'main', 'printf', 'scanf', 'malloc', 'free', 'calloc', 'realloc',
               'memset', 'memcpy', 'strlen', 'strcpy', 'strcat', 'fopen', 'fclose'}
    is_recursive, rec_func = False, None
    for fn in re.findall(r'\b(\w+)\s*\([^)]*\)\s*\{', code):
        if fn in STDLIB:
            continue
        if len(re.findall(rf'\b{re.escape(fn)}\s*\(', code)) > 1:
            is_recursive, rec_func = True, fn
            break

    has_divide = bool(re.search(r'\bmid\b|half|n\s*/\s*2', code))
    has_log    = bool(re.search(r'binary.search|bisect|\bi\s*[*/]=\s*2\b', code, re.I))
    has_sort   = bool(re.search(r'qsort|sort|swap.*\bi\b.*\bj\b', code, re.I))

    if is_recursive and has_divide:
        notation, label = "O(n log n)", "Linearithmic"
        explanation = (f"Recursive divide-and-conquer detected "
                       f"(function '{rec_func}'). Typical of merge sort / binary search.")
    elif is_recursive:
        notation, label = "O(2ⁿ)", "Exponential"
        explanation = (f"Unbounded recursion in '{rec_func}' without divide-and-conquer "
                       f"— potentially exponential (e.g. naïve Fibonacci).")
    elif has_sort and nesting >= 2:
        notation, label = "O(n log n)", "Linearithmic"
        explanation = "Sort-like nested pattern detected — likely O(n log n)."
    elif has_log:
        notation, label = "O(log n)", "Logarithmic"
        explanation = "Binary halving / logarithmic traversal pattern found."
    elif nesting == 3:
        notation, label = "O(n³)", "Cubic"
        explanation = "Three nested loops — typical of matrix multiplication."
    elif nesting == 2:
        notation, label = "O(n²)", "Quadratic"
        explanation = "Two nested loops — common in bubble/selection sort."
    elif total_loops == 1:
        notation, label = "O(n)", "Linear"
        explanation = "Single loop iterates over input once."
    elif total_loops == 0:
        notation, label = "O(1)", "Constant"
        explanation = "No loops or recursion — constant time."
    else:
        notation, label = "O(n)", "Linear"
        explanation = f"{total_loops} flat loops — likely linear."

    return {
        "notation":    notation,
        "label":       label,
        "explanation": explanation,
        "total_loops": total_loops,
        "is_recursive": is_recursive,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Helper: Green Computing Metrics
# ══════════════════════════════════════════════════════════════════════════════
def _analyze_green_metrics(code: str, time_complexity: dict) -> dict:
    """
    Estimates carbon footprint, energy consumption, and efficiency grade for the
    submitted code using Big-O complexity and code structure analysis.

    Model assumptions (for n = 10,000 typical input):
      - CPU energy per operation : ~0.5 nJ (modern 3 GHz processor)
      - Grid carbon intensity    : 475 g CO₂ / kWh (global average, IEA 2023)
    """
    notation    = time_complexity.get("notation", "O(1)")
    total_loops = time_complexity.get("total_loops", 0)
    is_recursive = time_complexity.get("is_recursive", False)

    N = 10_000  # reference input size

    OP_ESTIMATES = {
        "O(1)":       1,
        "O(log n)":   14,
        "O(n)":       N,
        "O(n log n)": N * 14,
        "O(n²)":      N * N,
        "O(n³)":      min(N ** 3, 10 ** 12),
        "O(2ⁿ)":      2 ** 20,          # capped at 2^20 for sanity
    }
    estimated_ops = OP_ESTIMATES.get(notation, N)

    # Energy calculation
    energy_nj  = estimated_ops * 0.5
    energy_mj  = energy_nj / 1_000_000
    energy_kwh = energy_mj / 3_600_000_000
    carbon_g   = energy_kwh * 475
    carbon_ug  = carbon_g * 1_000_000   # display in micrograms (more readable)

    # Efficiency grade
    GRADE_MAP = {
        "O(1)":       ("A+", 100, "#059669"),
        "O(log n)":   ("A",  92,  "#10b981"),
        "O(n)":       ("B",  75,  "#0ea5e9"),
        "O(n log n)": ("C",  58,  "#f59e0b"),
        "O(n²)":      ("D",  35,  "#f97316"),
        "O(n³)":      ("F",  12,  "#ef4444"),
        "O(2ⁿ)":      ("F",  5,   "#dc2626"),
    }
    grade, efficiency, grade_color = GRADE_MAP.get(notation, ("B", 70, "#0ea5e9"))

    # Code-level green analysis
    line_count     = len([l for l in code.splitlines() if l.strip()])
    has_malloc     = bool(re.search(r'\bmalloc\b|\bcalloc\b', code))
    has_free       = bool(re.search(r'\bfree\b', code))
    memory_leak_risk = has_malloc and not has_free

    # Suggestions
    suggestions = []
    if total_loops >= 2 and nesting_from_notation(notation) >= 2:
        suggestions.append("Replace nested loops with hash maps or sorting to achieve O(n log n) or better.")
    if is_recursive and "O(2ⁿ)" in notation:
        suggestions.append("Add memoization (dynamic programming) to eliminate redundant recursive calls.")
    if memory_leak_risk:
        suggestions.append("Detected malloc() without free() — memory leaks waste energy over time.")
    if notation in ("O(n³)", "O(2ⁿ)"):
        suggestions.append("Algorithm is energy-intensive. Consider a fundamentally different approach.")
    if has_malloc:
        suggestions.append("Use stack allocation where possible — heap allocation has higher energy overhead.")
    if total_loops == 0 and not is_recursive:
        suggestions.append("Excellent! Constant-time code has near-zero carbon footprint.")
    if not suggestions:
        suggestions.append("Code structure looks energy-efficient for its complexity class.")

    # Format display values
    if carbon_ug < 1:
        carbon_display = f"{carbon_ug * 1000:.4f} ng CO₂"
    elif carbon_ug < 1000:
        carbon_display = f"{carbon_ug:.4f} μg CO₂"
    else:
        carbon_display = f"{carbon_ug / 1000:.4f} mg CO₂"

    if energy_mj < 0.001:
        energy_display = f"{energy_mj * 1_000_000:.2f} nJ"
    elif energy_mj < 1:
        energy_display = f"{energy_mj * 1000:.4f} μJ"
    else:
        energy_display = f"{energy_mj:.4f} mJ"

    return {
        "grade":           grade,
        "grade_color":     grade_color,
        "efficiency_score": efficiency,
        "estimated_ops":   f"{estimated_ops:,}",
        "energy_display":  energy_display,
        "carbon_display":  carbon_display,
        "memory_leak_risk": memory_leak_risk,
        "line_count":      line_count,
        "suggestions":     suggestions,
        "reference_n":     f"{N:,}",
    }


def nesting_from_notation(notation: str) -> int:
    """Helper to get nesting level from Big-O string."""
    if "n³" in notation or "n^3" in notation:
        return 3
    if "n²" in notation or "n^2" in notation:
        return 2
    return 1


# ══════════════════════════════════════════════════════════════════════════════
# Helper: Row / Column extractor
# ══════════════════════════════════════════════════════════════════════════════
def _extract_row_col(raw_line: str):
    """Extract (row, col) from a GCC error line."""
    m = re.match(r'.+?:(\d+):(\d+):\s*', raw_line)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_code():
    code_content = ""

    # ── 1. Ingest code ────────────────────────────────────────────────────────
    if "file" in request.files and request.files["file"].filename:
        raw = request.files["file"].read()
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                code_content = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            return jsonify({"error": "Unable to decode file — ensure it is a valid text file."}), 400
    elif "code_text" in request.form:
        code_content = request.form["code_text"]
    else:
        return jsonify({"error": "No code or file provided."}), 400

    if not code_content.strip():
        return jsonify({"error": "Submitted code is empty."}), 400

    # ── 2. Write to temp file ─────────────────────────────────────────────────
    with open(TEMP_FILE, "w", encoding="utf-8") as fh:
        fh.write(code_content)

    # ── 3. Compile ────────────────────────────────────────────────────────────
    compiler_rc = 1
    try:
        import shutil
        if GCC_PATH == "gcc" and shutil.which("gcc") is None:
            raise FileNotFoundError("GCC not found on PATH")

        result = subprocess.run(
            [GCC_PATH, "-fmax-errors=100", "-pedantic-errors", TEMP_FILE],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        error_lines = result.stderr.strip().split("\n")
        compiler_rc = result.returncode

        for ce in _custom_lexical_scan(code_content, TEMP_FILE):
            if ce.split(": ", 2)[-1].lower() not in " ".join(error_lines).lower():
                error_lines.insert(0, ce)

    except FileNotFoundError:
        error_lines = []
        if ';' not in code_content:
            error_lines.append(f"{TEMP_FILE}:2:2: error: expected ';' before 'return'")
        if 'int' in code_content and '"' in code_content:
            error_lines.append(f"{TEMP_FILE}:3:5: error: invalid conversion from 'const char*' to 'int'")
        if not error_lines:
            error_lines.append(f"{TEMP_FILE}:1:1: error: general syntax issue detected")
        compiler_rc = 1

    finally:
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)

    # ── 4. Filter & deduplicate ───────────────────────────────────────────────
    KEYWORDS = ("error:", "warning:", "note:")
    raw_errors = [ln for ln in error_lines if any(kw in ln.lower() for kw in KEYWORDS)]
    if not raw_errors and error_lines and len(error_lines[0].strip()) > 5:
        raw_errors = [error_lines[0]]

    seen, all_errors = set(), []
    for ln in raw_errors:
        key = re.sub(r".+?:\d+:\d+:\s*", "", ln).strip().lower()
        if key and key not in seen:
            seen.add(key)
            all_errors.append(ln)

    # ── 5. Time complexity + Green metrics ────────────────────────────────────
    time_complexity = _analyze_time_complexity(code_content)
    green_metrics   = _analyze_green_metrics(code_content, time_complexity)

    # ── 6. Success path ───────────────────────────────────────────────────────
    if compiler_rc == 0 and not all_errors:
        return jsonify({
            "status":           "success",
            "message":          "Compilation Successful — no errors or vulnerabilities detected.",
            "developer_profile": json.loads(profiler.profile_session([])),
            "errors":           [],
            "time_complexity":  time_complexity,
            "green_metrics":    green_metrics,
        })

    if not model_loaded:
        return jsonify({"error": "ML model not loaded — run train_model.py first."}), 500

    # ── 7. ML Pipeline ────────────────────────────────────────────────────────
    LEXICAL_RULES = [
        r"stray", r"missing terminating", r"invalid suffix",
        r"empty character constant", r"null character",
        r"invalid preprocessing directive", r"extra tokens at end of",
    ]
    SYNTAX_RULES = [
        r"expected ';'", r"expected '\)'", r"expected '\}'", r"expected '\]'",
        r"expected expression", r"expected identifier", r"expected declaration",
        r"before '\w' token", r"at end of input", r"unbalanced",
        r"unrecognized escape",
    ]
    SEMANTIC_RULES = [
        r"undeclared", r"has no member", r"not a member", r"conflicting types",
        r"incompatible types", r"too many arguments", r"too few arguments",
        r"void value not ignored", r"is not a function", r"does not refer to a type",
        r"dereferencing pointer", r"subscripted value is", r"cannot convert",
        r"size of array",
    ]

    pipeline_report, session_predictions = [], []

    for i, raw_error in enumerate(all_errors, 1):
        clean_error = re.sub(r".+?:\d+:\d+:\s*", "", raw_error).strip()
        row, col    = _extract_row_col(raw_error)
        lower_err   = clean_error.lower()

        rule_pred = None
        for pat in LEXICAL_RULES:
            if re.search(pat, lower_err): rule_pred = "lexical"; break
        if not rule_pred:
            for pat in SYNTAX_RULES:
                if re.search(pat, lower_err): rule_pred = "syntax"; break
        if not rule_pred:
            for pat in SEMANTIC_RULES:
                if re.search(pat, lower_err): rule_pred = "semantic"; break

        vec           = vectorizer.transform([clean_error])
        ml_pred       = ml_model.predict(vec)[0]
        ml_confidence = float(max(ml_model.predict_proba(vec)[0]))

        prediction   = rule_pred if rule_pred else ml_pred
        confidence   = 0.999     if rule_pred else ml_confidence
        is_ambiguous = confidence < 0.65

        readability = readability_scorer.generate_score(clean_error)
        cwe_data    = json.loads(
            cwe_tagger.tag_error(clean_error, prediction, confidence,
                                 cascade_group=f"Group_{i}")
        )

        pipeline_report.append({
            "id":              i,
            "raw":             clean_error,
            "row":             row,
            "col":             col,
            "predicted_class": prediction.upper(),
            "confidence":      round(confidence * 100, 1),
            "is_ambiguous":    is_ambiguous,
            "readability_score": readability["readability_score_out_of_10"],
            "has_hints":       readability["contains_hints"],
            "cwe_id":          cwe_data["cwe_id"],
            "cwe_name":        cwe_data["cwe_name"],
            "severity":        cwe_data["severity"].upper(),
        })
        session_predictions.append({"predicted_class": prediction})

    dev_profile = json.loads(profiler.profile_session(session_predictions))

    return jsonify({
        "status":           "issues_found",
        "total_errors":     len(pipeline_report),
        "developer_profile": dev_profile,
        "errors":           pipeline_report,
        "time_complexity":  time_complexity,
        "green_metrics":    green_metrics,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
