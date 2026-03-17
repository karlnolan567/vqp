import pandas as pd
from engine.signals import score_signal
from engine.indices import calculate_index
from engine.patterns import detect_patterns, generate_alerts
from models import init_db, Client, Signal, SignalResult, Upload, IndexResult, PatternResult, Alert
from sqlalchemy.orm import sessionmaker
from utils.config_loader import load_config, get_signal_config
import os

def seed():
    # 1. Setup DB
    engine = init_db("sqlite:///vqp_prototype.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 2. Setup Clients
    clients = ["Pharma Global Corp", "BioTech Solutions", "Generic Labs Ltd"]
    for c_name in clients:
        if not session.query(Client).filter_by(client_name=c_name).first():
            session.add(Client(client_name=c_name))
    session.commit()
    
    # 3. Load Data & Config
    df = pd.read_csv("sample_vqp_data.csv")
    config = load_config()
    signals = session.query(Signal).all()
    sig_name_to_id = {s.signal_name: s.signal_id for s in signals}
    
    # 4. Process a few batches for each client
    db_clients = session.query(Client).all()
    for i, client in enumerate(db_clients):
        # Pick a different scenario for each client from the CSV
        scenario_idx = i % len(df)
        row = df.iloc[scenario_idx]
        
        new_upload = Upload(client_id=client.client_id, source_file="demo_seed.csv")
        session.add(new_upload)
        session.commit()
        
        signal_results = []
        for col in df.columns:
            sig_id = sig_name_to_id.get(col, col)
            val = float(row[col])
            score = score_signal(val, get_signal_config(sig_id, config))
            sr = SignalResult(upload_id=new_upload.upload_id, signal_id=sig_id, raw_value=val, normalized_score=score, trend=0.0, confidence=0.9)
            session.add(sr)
            signal_results.append(sr)
        
        # Indices
        idx_res = IndexResult(upload_id=new_upload.upload_id)
        w = config.get("index_weights", {})
        idx_res.ssi = calculate_index([s for s in signal_results if s.signal_id in w.get("SSI", {})], w.get("SSI", {}))
        idx_res.fi = calculate_index([s for s in signal_results if s.signal_id in w.get("FI", {})], w.get("FI", {}))
        idx_res.ri = calculate_index([s for s in signal_results if s.signal_id in w.get("RI", {})], w.get("RI", {}))
        idx_res.qci = calculate_index([s for s in signal_results if s.signal_id in w.get("QCI", {})], w.get("QCI", {}))
        idx_res.bei = calculate_index([s for s in signal_results if s.signal_id in w.get("BEI", {})], w.get("BEI", {}))
        indices = [idx_res.ssi, idx_res.fi, idx_res.ri, idx_res.qci, idx_res.bei]
        idx_res.quality_maturity_score = sum(indices) / len(indices)
        session.add(idx_res)
        
        # Patterns & Alerts
        patterns = detect_patterns(signal_results, config.get("patterns", []), new_upload.upload_id)
        for p in patterns: session.add(p)
        alerts = generate_alerts(patterns, new_upload.upload_id)
        for a in alerts: session.add(a)
        
    session.commit()
    print("Demo data seeded successfully into vqp_prototype.db")
    session.close()

if __name__ == "__main__":
    seed()
