import pytest
import pandas as pd
from engine.ingest import validate_columns, map_to_signals

# --- Ingestion Boundary & Edge Case Tests ---
def test_validate_columns_empty():
    df = pd.DataFrame() # Fully empty
    assert validate_columns(df, ["A"]) is False
    assert validate_columns(pd.DataFrame({"A": [1]}), []) is True # No requirements

def test_map_to_signals_missing_columns():
    df = pd.DataFrame({"A": [1]})
    # Mapping a non-existent column name should not crash
    signal_map = {"B": "S001"}
    mapped_df = map_to_signals(df, signal_map)
    assert "S001" not in mapped_df.columns
    assert "A" in mapped_df.columns

def test_map_to_signals_rename_partial():
    df = pd.DataFrame({"A": [1], "B": [2]})
    signal_map = {"A": "S1"}
    mapped_df = map_to_signals(df, signal_map)
    assert list(mapped_df.columns) == ["S1", "B"]

def test_process_malformed_numeric_data():
    # Streamlit/Pandas might ingest strings in numeric columns
    df = pd.DataFrame({"A": ["1", "2.5", "invalid"]})
    # Logic in app.py will handle float conversion
    # Let's verify standard pd.to_numeric behavior we rely on
    with pytest.raises(ValueError):
        pd.to_numeric(df["A"]).mean()
    
    # Correct handling (errors='coerce')
    clean_vals = pd.to_numeric(df["A"], errors='coerce')
    assert clean_vals.isna().sum() == 1
    assert clean_vals.mean() == pytest.approx(1.75) # (1 + 2.5) / 2
