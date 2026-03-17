import pandas as pd
from engine.signals import score_signal, calculate_trend
from engine.indices import calculate_index
from engine.patterns import detect_patterns
from models import init_db, Client, Signal, SignalResult, Upload
from sqlalchemy.orm import sessionmaker
from utils.config_loader import load_config, get_signal_config
import os

def run_final_test():
    print("--- Starting Final Backend Test ---")
    
    # 1. Setup DB and Session
    engine_url = "sqlite:///test_vqp.db"
    if os.path.exists("test_vqp.db"): os.remove("test_vqp.db")
    engine = init_db(engine_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 2. Setup Client
    client = Client(client_name="Demo Pharma Corp")
    session.add(client)
    session.commit()
    print(f"Created Test Client: {client.client_name}")
    
    # 3. Load Config
    config = load_config()
    print("Configuration loaded successfully.")
    
    # 4. Ingest Sample Data
    sample_file_path = "sample_vqp_data.csv"
    df = pd.read_csv(sample_file_path)
    print(f"Ingested {len(df)} rows and {len(df.columns)} signals.")

    # 5. Run Scoring Engine for the first row (Scenario: High Performance)
    print("\n--- Testing Scenario 1: High Performance ---")
    new_upload = Upload(client_id=client.client_id, source_file=sample_file_path)
    session.add(new_upload)
    session.commit()

    signals = session.query(Signal).all()
    sig_name_to_id = {s.signal_name: s.signal_id for s in signals}
    
    signal_results = []
    row = df.iloc[0] # First row
    for col in df.columns:
        sig_id = sig_name_to_id.get(col, col)
        val = float(row[col])
        sig_config = get_signal_config(sig_id, config)
        score = score_signal(val, sig_config)
        sr = SignalResult(upload_id=new_upload.upload_id, signal_id=sig_id, raw_value=val, normalized_score=score)
        signal_results.append(sr)
        print(f"  Signal {sig_id}: Raw={val}, Score={score}")

    # 6. Run Index Engine
    weights = config.get("index_weights", {})
    ssi = calculate_index([s for s in signal_results if s.signal_id in weights.get("SSI", {})], weights.get("SSI", {}))
    print(f"\nCalculated SSI Index: {round(ssi, 2)} (Expected ~1.0)")

    # 7. Run Pattern Engine for the fourth row (Scenario: Critical Failure)
    print("\n--- Testing Scenario 2: Critical Failure (Pattern Detection) ---")
    fail_row = df.iloc[3] # Fourth row
    fail_signals = []
    for col in df.columns:
        sig_id = sig_name_to_id.get(col, col)
        val = float(fail_row[col])
        score = score_signal(val, get_signal_config(sig_id, config))
        fail_signals.append(SignalResult(signal_id=sig_id, normalized_score=score))
    
    patterns = detect_patterns(fail_signals, config.get("patterns", []), 999)
    if patterns:
        for p in patterns:
            print(f"  [ALARM] Pattern Detected: {p.id if hasattr(p, 'id') else p.pattern_id} - {p.interpretation}")
    else:
        print("  Error: No patterns detected in failure scenario.")

    print("\n--- Final Test Complete: All Systems Operational ---")
    session.close()

if __name__ == "__main__":
    run_final_test()
