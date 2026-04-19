import json

class CompilerFingerprintProfiler:
    """
    Week 8 Deliverable: Aggregates all errors in a compilation session to produce
    a session-level summary evaluating the developer's skill level.
    """
    def __init__(self):
        self.skill_levels = ["Beginner", "Intermediate", "Advanced"]
        
    def profile_session(self, error_predictions):
        """
        Takes a list of dictionaries, e.g. [{"predicted_class": "syntax"}, {"predicted_class": "semantic"}]
        Returns a session level profile JSON.
        """
        if not error_predictions:
            return self._empty_profile()
            
        total_errors = len(error_predictions)
        syntax_count = sum(1 for e in error_predictions if e.get("predicted_class", "").lower() == "syntax")
        semantic_count = sum(1 for e in error_predictions if e.get("predicted_class", "").lower() == "semantic")
        lexical_count = sum(1 for e in error_predictions if e.get("predicted_class", "").lower() == "lexical")
        
        syntax_ratio = syntax_count / total_errors
        semantic_ratio = semantic_count / total_errors
        
        # Heuristics for developer skill level
        if syntax_ratio > 0.60 or total_errors > 15:
            dev_level = "Beginner (High Syntax Error Rate)"
        elif semantic_ratio > 0.60:
            dev_level = "Intermediate (High Semantic/Logic Focus)"
        else:
            dev_level = "Advanced (Balanced / Typing Typos)"
            
        dominant_category = max(
            [("syntax", syntax_count), ("semantic", semantic_count), ("lexical", lexical_count)], 
            key=lambda item: item[1]
        )[0]
        
        profile = {
            "total_errors_in_session": total_errors,
            "error_distribution": {
                "syntax": syntax_count,
                "semantic": semantic_count,
                "lexical": lexical_count
            },
            "dominant_error_category": dominant_category.upper(),
            "estimated_developer_skill": dev_level
        }
        return json.dumps(profile, indent=4)

    def _empty_profile(self):
        return json.dumps({
            "total_errors_in_session": 0,
            "estimated_developer_skill": "Unknown (Zero Errors)"
        }, indent=4)

if __name__ == "__main__":
    # Test execution
    mock_session = [
        {"predicted_class": "syntax"},
        {"predicted_class": "syntax"},
        {"predicted_class": "semantic"},
        {"predicted_class": "lexical"}
    ]
    profiler = CompilerFingerprintProfiler()
    print(profiler.profile_session(mock_session))
