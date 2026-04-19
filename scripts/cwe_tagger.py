import json

class CWETagger:
    """
    Week 10 Deliverable: First-class CWE Tagger module with curated mapping.
    Auto-assigns a CWE ID from a curated table for semantic predictions.
    """
    def __init__(self):
        self.cwe_mapping = {
            "pointer": {"cwe_id": "CWE-476", "cwe_name": "NULL Pointer Dereference", "severity": "HIGH"},
            "null": {"cwe_id": "CWE-476", "cwe_name": "NULL Pointer Dereference", "severity": "HIGH"},
            "bounds": {"cwe_id": "CWE-119", "cwe_name": "Improper Restriction of Operations within Bounds", "severity": "HIGH"},
            "array subscript": {"cwe_id": "CWE-119", "cwe_name": "Improper Restriction of Operations within Bounds", "severity": "HIGH"},
            "format": {"cwe_id": "CWE-134", "cwe_name": "Use of Externally-Controlled Format String", "severity": "MEDIUM"},
            "free": {"cwe_id": "CWE-416", "cwe_name": "Use After Free", "severity": "CRITICAL"},
            "unallocated": {"cwe_id": "CWE-415", "cwe_name": "Double Free", "severity": "CRITICAL"},
            "address": {"cwe_id": "CWE-562", "cwe_name": "Return of Stack Variable Address", "severity": "MEDIUM"},
            "overflow": {"cwe_id": "CWE-120", "cwe_name": "Buffer Copy without Checking Size of Input", "severity": "HIGH"}
        }

    def tag_error(self, error_text, predicted_class, confidence=1.0, cascade_group="root"):
        """
        Extends the system output format to include CWE fields based on mapping.
        """
        cwe_data = {
            "cwe_id": None,
            "cwe_name": "No immediate security threat",
            "severity": "LOW"
        }
        
        error_lower = error_text.lower()
        if predicted_class.lower() == "semantic":
            # Search curated mapping table
            for keyword, data in self.cwe_mapping.items():
                if keyword in error_lower:
                    cwe_data = data
                    break
            
            # Fallback for semantic logic flaw
            if cwe_data["cwe_id"] is None:
                cwe_data = {
                    "cwe_id": "CWE-699", 
                    "cwe_name": "Software Development / Logic Flaw", 
                    "severity": "LOW"
                }

        # Week 10 Requirements: Extended system output JSON schema
        json_schema = {
            "error_text": error_text,
            "predicted_class": predicted_class.upper(),
            "confidence": round(confidence, 2),
            "cascade_group": cascade_group,
            "cwe_id": cwe_data["cwe_id"],
            "cwe_name": cwe_data["cwe_name"],
            "severity": cwe_data["severity"]
        }
        
        return json.dumps(json_schema, indent=4)

if __name__ == "__main__":
    tagger = CWETagger()
    print(tagger.tag_error("warning: value stored to 'x' is never read resulting in dereg of null", "semantic", 0.95))
