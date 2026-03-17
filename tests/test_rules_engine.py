import pytest
from engine.signals import score_signal, calculate_trend
from engine.indices import calculate_index, get_quadrant
from engine.patterns import detect_patterns
from models import SignalResult

# --- Signal Scoring Boundary Tests ---
def test_score_signal_boundaries():
    config = {"thresholds": [5, 10], "scores": [1.0, 0.5, 0.1], "logic": "negative"}
    # Exact threshold matches
    assert score_signal(5, config) == 1.0  # Should include the boundary (<= 5)
    assert score_signal(10, config) == 0.5 # Should include the boundary (<= 10)
    # Edge cases
    assert score_signal(0, config) == 1.0   # Minimum possible
    assert score_signal(100, config) == 0.1 # Far beyond last threshold
    assert score_signal(-5, config) == 1.0  # Negative values (should be treated as low)

def test_score_signal_empty_config():
    assert score_signal(10, {}) == 0.5 # Should return default score

# --- Index Calculation Edge Cases ---
def test_calculate_index_edge_cases():
    weights = {"S1": 1.0}
    # Empty signals list
    assert calculate_index([], weights) == 0.0
    # Signals with no matching weights
    signals = [SignalResult(signal_id="UNKNOWN", normalized_score=1.0)]
    assert calculate_index(signals, weights) == 0.0
    # Weights with no matching signals
    signals = [SignalResult(signal_id="S1", normalized_score=1.0)]
    assert calculate_index(signals, {"S2": 1.0}) == 0.0
    # All scores zero
    signals = [SignalResult(signal_id="S1", normalized_score=0.0)]
    assert calculate_index(signals, weights) == 0.0

# --- Trend Calculation Boundaries ---
def test_calculate_trend_boundaries():
    assert calculate_trend(100, 100) == 0.0 # No change
    assert calculate_trend(200, 100) == 1.0 # 100% increase
    assert calculate_trend(0, 100) == -1.0  # 100% decrease
    assert calculate_trend(100, 0) == 0.0   # Division by zero handled
    assert calculate_trend(100, None) == 0.0 # Null handling

# --- Pattern Detection Logic Boundaries ---
def test_detect_patterns_logic_edges():
    pattern_configs = [{
        "id": "P1", "name": "T", "signals": ["S1", "S2"], 
        "logic": "both_low_score", "threshold": 0.5, "interpretation": "X"
    }]
    # Exactly on the threshold (Both 0.5 should trigger)
    signals = [
        SignalResult(signal_id="S1", normalized_score=0.5),
        SignalResult(signal_id="S2", normalized_score=0.5)
    ]
    results = detect_patterns(signals, pattern_configs, 1)
    assert len(results) == 1
    
    # One just above threshold (0.51) should NOT trigger 'both_low'
    signals[1].normalized_score = 0.51
    results = detect_patterns(signals, pattern_configs, 1)
    assert len(results) == 0

def test_detect_patterns_any_logic():
    pattern_configs = [{
        "id": "P1", "name": "T", "signals": ["S1", "S2"], 
        "logic": "any_low_score", "threshold": 0.3, "interpretation": "X"
    }]
    # One very low, one high
    signals = [
        SignalResult(signal_id="S1", normalized_score=0.1),
        SignalResult(signal_id="S2", normalized_score=1.0)
    ]
    results = detect_patterns(signals, pattern_configs, 1)
    assert len(results) == 1
    assert results[0].strength == pytest.approx(0.9) # 1.0 - 0.1
