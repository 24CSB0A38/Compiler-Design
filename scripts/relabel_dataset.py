import pandas as pd
import os
import re

# Paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(_SCRIPT_DIR, "..", "dataset", "clacer_dataset.csv")

def relabel_errors(df):
    """
    Apply heuristic rules to fix mislabeled data in the CLACER dataset.
    """
    lexical_keywords = [
        r"stray", r"missing terminating", r"invalid suffix", 
        r"empty character constant", r"null character", r"digit",
        r"stray '\\'", r"stray '@'", r"stray '`'"
    ]
    
    syntax_keywords = [
        r"expected ';'", r"expected '\}'", r"expected '\)'", 
        r"expected '\]'", r"expected identifier", r"expected expression",
        r"before 'return'", r"at end of input", r"duplicate label",
        r"unrecognized command line option"
    ]
    
    semantic_keywords = [
        r"undeclared", r"undeclared here", r"has no member", 
        r"not a member", r"conflicting types", r"incompatible types",
        r"invalid conversion", r"too many arguments", r"too few arguments",
        r"subscripted value is neither array nor pointer", r"size of array",
        r"dereferencing pointer", r"void value not ignored", r"not a function"
    ]

    def get_correct_label(msg, current_label):
        msg_lower = str(msg).lower()
        
        # 1. Check Lexical (highest priority for "stray" etc)
        for pattern in lexical_keywords:
            if re.search(pattern, msg_lower):
                return "lexical"
        
        # 2. Check Syntax
        for pattern in syntax_keywords:
            if re.search(pattern, msg_lower):
                return "syntax"
                
        # 3. Check Semantic
        for pattern in semantic_keywords:
            if re.search(pattern, msg_lower):
                return "semantic"
        
        return current_label

    print("Applying data sanitization heuristics...")
    df['label'] = df.apply(lambda row: get_correct_label(row['error_message'], row['label']), axis=1)
    return df

def main():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    print(f"Loading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    
    original_lexical = len(df[df['label'] == 'lexical'])
    original_syntax = len(df[df['label'] == 'syntax'])
    original_semantic = len(df[df['label'] == 'semantic'])

    df = relabel_errors(df)

    new_lexical = len(df[df['label'] == 'lexical'])
    new_syntax = len(df[df['label'] == 'syntax'])
    new_semantic = len(df[df['label'] == 'semantic'])

    print("\n==== RELABELING SUMMARY ====")
    print(f"LEXICAL:  {original_lexical} -> {new_lexical} ({new_lexical - original_lexical:+})")
    print(f"SYNTAX:   {original_syntax} -> {new_syntax} ({new_syntax - original_syntax:+})")
    print(f"SEMANTIC: {original_semantic} -> {new_semantic} ({new_semantic - original_semantic:+})")
    print("============================\n")

    df.to_csv(DATASET_PATH, index=False)
    print(f"✅ Success! Sanitized dataset saved to {DATASET_PATH}")

if __name__ == "__main__":
    main()
