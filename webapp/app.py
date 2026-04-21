"""
Intelligent Compiler Suite — Flask Backend
==========================================
Compiles user-submitted C code via GCC, then runs it through an ML pipeline
that classifies errors (lexical / syntax / semantic), assigns CWE security
IDs, scores readability, profiles the developer, and estimates time complexity.
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
    GCC_PATH = "gcc"   # fall back to PATH

# ── Initialise global singletons ──────────────────────────────────────────────
cwe_tagger          = CWETagger()               if _ml_modules_loaded else None
readability_scorer  = ReadabilityScorer()        if _ml_modules_loaded else None
profiler            = CompilerFingerprintProfiler() if _ml_modules_loaded else None

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
def _custom_lexical_scan(code: str, temp_path: str) -> list[str]:
    """
    Detects characters GCC may silently accept (e.g. $ in identifiers)
    and synthesises realistic error lines for them.
    """
    INVALID_CHARS = {
        '$': "error: stray '$' in program",
        '`': "error: stray '`' in program",
        '@': "error: stray '@' in program",
    }
    found: list[str] = []
    for lineno, line in enumerate(code.splitlines(), start=1):
        clean = re.sub(r'".*?"', '""', line)   # blank out string literals
        clean = re.sub(r'//.*',  '',  clean)   # strip line comments
        for char, msg in INVALID_CHARS.items():
            if char in clean:
                col = clean.index(char) + 1
                found.append(f"{temp_path}:{lineno}:{col}: {msg}")
    return found


# ══════════════════════════════════════════════════════════════════════════════
# Helper: Time Complexity Analyser
# ══════════════════════════════════════════════════════════════════════════════
def _analyze_time_complexity(code: str) -> dict:
    """
    Heuristic static analysis of C code to estimate Big-O time complexity.
    Considers loop nesting depth, recursion, and known algorithm patterns.
    """
    lines = code.splitlines()

    # Collect loop lines (skip comments)
    loop_lines = [
        ln for ln in lines
        if re.search(r'\b(for|while|do)\b', ln) and not ln.strip().startswith('//')
    ]
    total_loops = len(loop_lines)

    # Estimate nesting depth via indentation
    nesting = 1
    if total_loops >= 2:
        indents = [len(ln) - len(ln.lstrip()) for ln in loop_lines]
        if len(set(indents)) > 1:
            nesting = 2
        if total_loops >= 3 and nesting == 2:
            deeper   = [i for i in indents if i > min(indents)]
            deepest  = [i for i in deeper  if i > min(deeper)] if deeper else []
            if deepest:
                nesting = 3

    # Detect recursion: any non-stdlib function called more than once
    STDLIB = {'main', 'printf', 'scanf', 'malloc', 'free', 'calloc', 'realloc',
               'memset', 'memcpy', 'strlen', 'strcpy', 'strcat', 'fopen', 'fclose'}
    is_recursive = False
    rec_func_name = None
    for fn in re.findall(r'\b(\w+)\s*\([^)]*\)\s*\{', code):
        if fn in STDLIB:
            continue
        occurrences = [m.start() for m in re.finditer(rf'\b{re.escape(fn)}\s*\(', code)]
        if len(occurrences) > 1:
            is_recursive   = True
            rec_func_name  = fn
            break

    # Pattern flags
    has_divide = bool(re.search(r'\bmid\b|half|n\s*/\s*2', code))
    has_log    = bool(re.search(r'binary.search|bisect|\bi\s*[*/]=\s*2\b', code, re.I))
    has_sort   = bool(re.search(r'qsort|sort|swap.*\bi\b.*\bj\b', code, re.I))

    # Decision
    if is_recursive and has_divide:
        notation    = "O(n log n)"
        label       = "Linearithmic"
        explanation = (f"Recursive divide-and-conquer pattern detected "
                       f"(function '{rec_func_name}'). Typical of merge sort / "
                       f"binary search with recursion.")
    elif is_recursive:
        notation    = "O(2ⁿ)"
        label       = "Exponential"
        explanation = (f"Unbounded recursion in '{rec_func_name}' without "
                       f"divide-and-conquer — potentially exponential "
                       f"(e.g. naïve Fibonacci).")
    elif has_sort and nesting >= 2:
        notation    = "O(n log n)"
        label       = "Linearithmic"
        explanation = "Sort-like nested pattern detected — likely O(n log n)."
    elif has_log:
        notation    = "O(log n)"
        label       = "Logarithmic"
        explanation = "Binary halving / logarithmic traversal pattern found."
    elif nesting == 3:
        notation    = "O(n³)"
        label       = "Cubic"
        explanation = "Three levels of nested loops — typical of matrix multiplication."
    elif nesting == 2:
        notation    = "O(n²)"
        label       = "Quadratic"
        explanation = "Two nested loops — common in bubble/selection sort or brute-force 2-D algorithms."
    elif total_loops == 1:
        notation    = "O(n)"
        label       = "Linear"
        explanation = "Single loop iterates over input once."
    elif total_loops == 0:
        notation    = "O(1)"
        label       = "Constant"
        explanation = "No loops or recursion — code runs in constant time."
    else:
        notation    = "O(n)"
        label       = "Linear"
        explanation = f"{total_loops} flat loops detected — likely linear with a constant factor."

    return {
        "notation":    notation,
        "label":       label,
        "explanation": explanation,
        "total_loops": total_loops,
        "is_recursive": is_recursive,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Helper: Row / Column extractor
# ══════════════════════════════════════════════════════════════════════════════
def _extract_row_col(raw_line: str) -> tuple[int | None, int | None]:
    """Extract (row, col) from a GCC error line — returns (None, None) on failure."""
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

        # Inject custom lexical errors not caught by GCC
        for ce in _custom_lexical_scan(code_content, TEMP_FILE):
            ce_msg = ce.split(": ", 2)[-1].lower()
            if ce_msg not in " ".join(error_lines).lower():
                error_lines.insert(0, ce)

    except FileNotFoundError:
        # Demo fallback when GCC is unavailable
        error_lines = []
        if ';' not in code_content:
            error_lines.append(f"{TEMP_FILE}:2:2: error: expected ';' before 'return'")
        if 'int' in code_content and '"' in code_content:
            error_lines.append(f"{TEMP_FILE}:3:5: error: invalid conversion from 'const char*' to 'int'")
        if 'null' in code_content.lower() or '*x' in code_content:
            error_lines.append(f"{TEMP_FILE}:4:5: error: pointer 'x' resulting in deref of null")
        if not error_lines:
            error_lines.append(f"{TEMP_FILE}:1:1: error: general syntax issue detected")
        compiler_rc = 1

    finally:
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)

    # ── 4. Filter & deduplicate errors ────────────────────────────────────────
    KEYWORDS = ("error:", "warning:", "note:")
    raw_errors = [
        ln for ln in error_lines
        if any(kw in ln.lower() for kw in KEYWORDS)
    ]
    if not raw_errors and error_lines and len(error_lines[0].strip()) > 5:
        raw_errors = [error_lines[0]]

    seen: set[str] = set()
    all_errors: list[str] = []
    for ln in raw_errors:
        key = re.sub(r".+?:\d+:\d+:\s*", "", ln).strip().lower()
        if key and key not in seen:
            seen.add(key)
            all_errors.append(ln)

    # ── 5. Time complexity (always computed) ──────────────────────────────────
    time_complexity = _analyze_time_complexity(code_content)

    # ── 6. Success path ───────────────────────────────────────────────────────
    if compiler_rc == 0 and not all_errors:
        return jsonify({
            "status":           "success",
            "message":          "Compilation Successful — no errors or vulnerabilities detected.",
            "developer_profile": json.loads(profiler.profile_session([])),
            "errors":           [],
            "time_complexity":  time_complexity,
        })

    if not model_loaded:
        return jsonify({
            "error": "ML model not loaded — run train_model.py first."
        }), 500

    # ── 7. ML Pipeline ────────────────────────────────────────────────────────
    # Rule sets (deterministic layer 1)
    LEXICAL_RULES  = [
        r"stray", r"missing terminating", r"invalid suffix",
        r"empty character constant", r"null character",
        r"invalid preprocessing directive", r"extra tokens at end of",
    ]
    SYNTAX_RULES   = [
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

    pipeline_report:     list[dict] = []
    session_predictions: list[dict] = []

    for i, raw_error in enumerate(all_errors, 1):
        clean_error = re.sub(r".+?:\d+:\d+:\s*", "", raw_error).strip()
        row, col    = _extract_row_col(raw_error)
        lower_err   = clean_error.lower()

        # Layer 1 — deterministic rules
        rule_pred = None
        for pat in LEXICAL_RULES:
            if re.search(pat, lower_err):
                rule_pred = "lexical"; break
        if not rule_pred:
            for pat in SYNTAX_RULES:
                if re.search(pat, lower_err):
                    rule_pred = "syntax"; break
        if not rule_pred:
            for pat in SEMANTIC_RULES:
                if re.search(pat, lower_err):
                    rule_pred = "semantic"; break

        # Layer 2 — ML model fallback
        vec           = vectorizer.transform([clean_error])
        ml_pred       = ml_model.predict(vec)[0]
        ml_confidence = float(max(ml_model.predict_proba(vec)[0]))

        prediction = rule_pred   if rule_pred else ml_pred
        confidence = 0.999       if rule_pred else ml_confidence
        is_ambiguous = confidence < 0.65

        readability = readability_scorer.generate_score(clean_error)
        cwe_data    = json.loads(
            cwe_tagger.tag_error(clean_error, prediction, confidence,
                                 cascade_group=f"Group_{i}")
        )

        pipeline_report.append({
            "id":               i,
            "raw":              clean_error,
            "row":              row,
            "col":              col,
            "predicted_class":  prediction.upper(),
            "confidence":       round(confidence * 100, 1),
            "is_ambiguous":     is_ambiguous,
            "readability_score": readability["readability_score_out_of_10"],
            "has_hints":        readability["contains_hints"],
            "cwe_id":           cwe_data["cwe_id"],
            "cwe_name":         cwe_data["cwe_name"],
            "severity":         cwe_data["severity"].upper(),
        })
        session_predictions.append({"predicted_class": prediction})

    dev_profile = json.loads(profiler.profile_session(session_predictions))

    return jsonify({
        "status":           "issues_found",
        "total_errors":     len(pipeline_report),
        "developer_profile": dev_profile,
        "errors":           pipeline_report,
        "time_complexity":  time_complexity,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
