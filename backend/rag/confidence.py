def calculate_confidence(search_results: list) -> float:
    if not search_results:
        return 0.0
    
    top_score = search_results[0].get('score', 0.0)
    return round(top_score, 2)

def should_escalate(confidence: float, threshold: float = 0.80) -> bool:
    return confidence < threshold