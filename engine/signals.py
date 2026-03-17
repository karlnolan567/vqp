from typing import Dict, Any
import numpy as np

def score_signal(raw_value: float, config: Dict[str, Any]) -> float:
    """
    Scoring logic:
    Positive logic: higher is better (e.g., Training Compliance)
    Negative logic: lower is better (e.g., Adverse Events)
    """
    thresholds = config.get("thresholds", [])
    scores = config.get("scores", [])
    logic = config.get("logic", "negative")
    
    if not thresholds or not scores:
        return 0.5 # Default score
        
    if logic == "negative":
        # Raw value <= threshold1: score1
        # threshold1 < Raw value <= threshold2: score2
        for i, t in enumerate(thresholds):
            if raw_value <= t:
                return scores[i]
        return scores[-1] # Beyond last threshold
    else:
        # Positive logic: Raw value >= threshold1: score1
        for i, t in enumerate(thresholds):
            if raw_value >= t:
                return scores[i]
        return scores[-1] # Below last threshold

def calculate_trend(current_value: float, previous_value: float) -> float:
    if previous_value == 0 or previous_value is None:
        return 0.0
    return (current_value - previous_value) / previous_value
