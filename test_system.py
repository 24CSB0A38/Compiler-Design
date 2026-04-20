import urllib.request, urllib.parse, json

tests = [
    ("lex10.c", open("error_programs/lexical/lex10.c").read()),
    ("dollar_sign", "int main() { int a$; }"),
    ("syntax", "int main() { int x = 5 }"),
    ("semantic", "int main() { printf(x); }"),
]

print("=== FULL SYSTEM TEST ===")
for name, code in tests:
    data = urllib.parse.urlencode({"code_text": code}).encode()
    req = urllib.request.Request("http://127.0.0.1:5000/analyze", data=data)
    with urllib.request.urlopen(req) as f:
        res = json.loads(f.read().decode())
    errors = res.get("errors", [])
    print(f"\n[{name}]  total={res.get('total_errors')}")
    for err in errors:
        print(f"  -> {err.get('predicted_class'):8} | {err.get('confidence')}% | {err.get('cwe_id')} | {err.get('raw')[:60]}")
print("\n=== DONE ===")
