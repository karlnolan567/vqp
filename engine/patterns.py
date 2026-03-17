from typing import List, Dict, Any
from models import SignalResult, PatternResult

def detect_patterns(signals: List[SignalResult], pattern_configs: List[Dict[str, Any]], upload_id: int) -> List[PatternResult]:
    """
    Evaluates defined patterns based on normalized signal scores.
    """
    results = []
    sig_scores = {s.signal_id: s.normalized_score for s in signals}
    
    for p in pattern_configs:
        relevant_scores = [sig_scores.get(sid) for sid in p["signals"] if sid in sig_scores]
        
        if not relevant_scores:
            continue
            
        active = False
        strength = 0.0
        
        if p["logic"] == "both_low_score":
            # All signals must be below threshold
            if all(s <= p["threshold"] for s in relevant_scores):
                active = True
                strength = 1.0 - (sum(relevant_scores) / len(relevant_scores))
                
        elif p["logic"] == "any_low_score":
            # At least one signal below threshold
            if any(s <= p["threshold"] for s in relevant_scores):
                active = True
                strength = 1.0 - min(relevant_scores)
                
        if active:
            results.append(PatternResult(
                upload_id=upload_id,
                pattern_id=p["id"],
                active=True,
                strength=strength,
                interpretation=p["interpretation"]
            ))
            
    return results

def generate_alerts(patterns: List[PatternResult], upload_id: int) -> List[Any]:
    """
    Converts active patterns into actionable alerts.
    """
    from models import Alert
    alerts = []
    for p in patterns:
        severity = "High" if p.strength > 0.7 else "Medium"
        alerts.append(Alert(
            upload_id=upload_id,
            alert_type="Pattern Detected",
            severity=severity,
            message=f"Critical Pattern '{p.pattern_id}' active. Interpretation: {p.interpretation}"
        ))
    return alerts
