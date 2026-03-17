import pandas as pd
from typing import Dict, Any, List, Tuple
import numpy as np

def validate_columns(df: pd.DataFrame, required_fields: List[str]) -> bool:
    return all(field in df.columns for field in required_fields)

def map_to_signals(df: pd.DataFrame, signal_map: Dict[str, str]) -> pd.DataFrame:
    """
    Maps spreadsheet columns to internal signal IDs.
    signal_map: { 'Column Name': 'signal_id' }
    """
    return df.rename(columns=signal_map)

def process_upload(file, session) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Ingests file, maps signals, and performs advanced validation (bounds + outliers).
    Returns (DataFrame, List of Warnings).
    """
    from models import Signal, SignalResult, Upload
    
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        raise ValueError("Unsupported file format.")
    
    # 1. Map Signals
    signals = session.query(Signal).all()
    signal_map = {}
    for sig in signals:
        if sig.signal_id in df.columns:
            signal_map[sig.signal_id] = sig.signal_id
        elif sig.signal_name in df.columns:
            signal_map[sig.signal_name] = sig.signal_id
            
    mapped_df = df.rename(columns=signal_map)
    available_signals = [sig.signal_id for sig in signals]
    mapped_df = mapped_df[[c for c in mapped_df.columns if c in available_signals]]
    
    # 2. Advanced Validation
    warnings = []
    
    for signal_id in mapped_df.columns:
        sig_data = mapped_df[signal_id]
        avg_val = sig_data.mean()
        
        # A. Logical Bound Checks
        # Assuming percentage signals follow S002, S004, S005, S007 patterns
        is_pct = any(p in signal_id for p in ['S002', 'S004', 'S005', 'S007'])
        if is_pct:
            if avg_val < 0 or avg_val > 1:
                warnings.append({
                    "level": "Error",
                    "signal_id": signal_id,
                    "msg": f"Value {avg_val:.2f} is out of percentage bounds (0-1)."
                })
        else:
            if avg_val < 0:
                warnings.append({
                    "level": "Error",
                    "signal_id": signal_id,
                    "msg": f"Value {avg_val:.2f} is out of count bounds (>=0)."
                })

        # B. Outlier Detection (Z-Score based on history)
        # Fetch all historical results for this signal
        hist_results = session.query(SignalResult.raw_value).filter_by(signal_id=signal_id).all()
        if len(hist_results) > 5:
            hist_vals = [h[0] for h in hist_results]
            mean = np.mean(hist_vals)
            std = np.std(hist_vals)
            
            if std > 0:
                z_score = abs(avg_val - mean) / std
                if z_score > 2.5: # 2.5 SD is a significant outlier
                    warnings.append({
                        "level": "Warning",
                        "signal_id": signal_id,
                        "msg": f"Anomalous detected: Value {avg_val:.2f} is {z_score:.1f} SD from mean."
                    })
    
    return mapped_df, warnings
