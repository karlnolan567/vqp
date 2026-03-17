from typing import List, Dict
from models import SignalResult

def calculate_index(signals: List[SignalResult], weights: Dict[str, float]) -> float:
    """
    Weighted calculation for a single index.
    index_score = sum(signal_score * signal_weight) / sum(weights)
    """
    if not signals or not weights:
        return 0.0
    
    total_score = 0.0
    total_weight = 0.0
    
    for sig in signals:
        if sig.signal_id in weights:
            weight = weights[sig.signal_id]
            total_score += sig.normalized_score * weight
            total_weight += weight
            
    if total_weight == 0:
        return 0.0
        
    return total_score / total_weight

def get_quadrant(fi_score: float, ri_score: float, thresholds: Dict[str, float]) -> str:
    """
    Assigns FI/RI quadrant based on thresholds.
    Q1: High FI, High RI
    Q2: Low FI, High RI
    Q3: Low FI, Low RI
    Q4: High FI, Low RI
    """
    fi_high = thresholds.get("FI_high", 0.7)
    ri_high = thresholds.get("RI_high", 0.7)
    
    if fi_score >= fi_high and ri_score >= ri_high:
        return "Quadrant 1 (Critical Risk)"
    elif fi_score < fi_high and ri_score >= ri_high:
        return "Quadrant 2 (Systemic Issues)"
    elif fi_score < fi_high and ri_score < ri_high:
        return "Quadrant 3 (Stable/Mature)"
    else:
        return "Quadrant 4 (Operational Risk)"
