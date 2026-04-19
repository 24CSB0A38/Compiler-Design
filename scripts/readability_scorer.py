import json

class ReadabilityScorer:
    """
    Week 12 Deliverable: Build Error Readability Scorer for compiler errors.
    Score range 0-10 based on length, hints, keyword density, etc.
    """
    def __init__(self):
        self.helpful_hints = ["did you mean", "expected", "maybe you meant", "note:", "declared here"]
        
    def generate_score(self, error_message):
        score = 0.0
        
        # 1. Message Length (Not too short, not too long) 0-3 points
        length = len(error_message)
        if 20 <= length <= 150:
            score += 3.0
        elif length < 20:
            score += 1.0 # Too cryptic
        else:
            score += 2.0 # Slightly too verbose
            
        # 2. Presence of fix hints (0-4 points)
        lower_msg = error_message.lower()
        hint_count = sum(1 for hint in self.helpful_hints if hint in lower_msg)
        score += min(4.0, hint_count * 2.0)
        
        # 3. Actionability / Density (0-3 points)
        # Standard errors containing punctuation showing exactly what's missing
        actionable_chars = ["'", ";", "{", "}", "\""]
        actionable_count = sum(1 for char in actionable_chars if char in error_message)
        score += min(3.0, actionable_count * 1.0)
        
        return {
            "error_message": error_message,
            "readability_score_out_of_10": round(score, 1),
            "contains_hints": hint_count > 0
        }

if __name__ == "__main__":
    scorer = ReadabilityScorer()
    print(scorer.generate_score("error: expected ';' before '}' token"))
