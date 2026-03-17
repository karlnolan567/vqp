import streamlit as st
import pandas as pd
import sqlalchemy
import json
from engine.ingest import process_upload
from engine.patterns import detect_patterns, generate_alerts
from utils.reports import generate_pdf_report
from models import init_db, Client, Upload, SignalResult, Signal, IndexResult, PatternResult, Alert
from sqlalchemy.orm import sessionmaker
from engine.signals import score_signal, calculate_trend
from engine.indices import calculate_index, get_quadrant
from utils.config_loader import load_config, get_signal_config
import plotly.express as px

# Setup Database
engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()

# Load Config
config = load_config()

# Streamlit UI
st.set_page_config(page_title="VirtualQP Prototype", layout="wide", page_icon="🧪")

# Custom Branding CSS
st.markdown("""
    <style>
    .brand-header {
        color: #003366;
        font-family: sans-serif;
        font-weight: bold;
        margin-bottom: 0px;
    }
    .brand-accent {
        color: #00A8A8;
    }
    .tagline {
        font-style: italic;
        color: #666;
        font-size: 0.85em;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Branding
st.sidebar.markdown("<h2 class='brand-header'>Virtual<span class='brand-accent'>QP</span></h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p class='tagline'>QMS Design | Quality as a Subscription</p>", unsafe_allow_html=True)
st.sidebar.divider()

page = st.sidebar.radio("Navigation", [
    "Portfolio Overview", 
    "Data Ingestion", 
    "Signal Review", 
    "Index Dashboard", 
    "Pattern & Alerts",
    "System Configuration"
])

# Global Header
st.markdown("<h1 class='brand-header'>Virtual<span class='brand-accent'>QP</span> | <span style='font-weight: normal; font-size: 0.7em;'>QMS Design Portal</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='tagline'>Your Quality Infrastructure Built Before You Need It</p>", unsafe_allow_html=True)
st.divider()

if page == "Portfolio Overview":
    st.header("Executive Portfolio Overview")
    
    total_clients = session.query(Client).count()
    total_uploads = session.query(Upload).count()
    avg_qms = session.query(IndexResult).with_entities(sqlalchemy.func.avg(IndexResult.quality_maturity_score)).scalar() or 0.0
    
    m_cols = st.columns(3)
    m_cols[0].metric("Total Clients", total_clients)
    m_cols[1].metric("Total Batches Processed", total_uploads)
    m_cols[2].metric("Average Portfolio QMS", round(avg_qms, 2))
    
    st.divider()
    
    st.subheader("Latest Client Performance")
    query = """
    SELECT c.client_name, u.upload_date, i.quality_maturity_score, i.fi, i.ri
    FROM clients c
    JOIN uploads u ON c.client_id = u.client_id
    JOIN index_results i ON u.upload_id = i.upload_id
    WHERE u.upload_id = (SELECT MAX(upload_id) FROM uploads WHERE client_id = c.client_id)
    """
    df_portfolio = pd.read_sql(query, engine)
    
    if not df_portfolio.empty:
        st.dataframe(df_portfolio, use_container_width=True)
        fig = px.scatter(df_portfolio, x="fi", y="ri", text="client_name", size="quality_maturity_score", 
                         color="quality_maturity_score", title="Client Risk Distribution (FI vs RI)",
                         labels={"fi": "Facility Index", "ri": "Regulatory Index"},
                         range_x=[0,1], range_y=[0,1])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data processed yet. Please enroll a client and process a batch in 'Data Ingestion'.")

elif page == "Data Ingestion":
    st.header("End-to-End Data Ingestion")
    
    st.subheader("Section 1: Site Selection & Enrollment")
    c_list, c_add = st.columns([2, 1])
    
    with c_add:
        with st.form("new_site_form", clear_on_submit=True):
            new_name = st.text_input("Enroll New Site")
            if st.form_submit_button("Enroll") and new_name:
                nc = Client(client_name=new_name)
                session.add(nc)
                session.commit()
                st.success(f"Enrolled: {new_name}")
                st.rerun()

    with c_list:
        clients = session.query(Client).all()
        client_names = [c.client_name for c in clients]
        selected_name = st.selectbox("Select Target Site", ["Select..."] + client_names)
        if selected_name != "Select...":
            st.success(f"Target Site Selected: **{selected_name}**")

    st.divider()

    st.subheader("Section 2: Batch Processing")
    if selected_name == "Select...":
        st.info("Please select a site in Section 1 to enable batch processing.")
    else:
        confirmed_client = session.query(Client).filter_by(client_name=selected_name).first()
        uploaded_file = st.file_uploader(f"Upload Batch Data for {confirmed_client.client_name}", type=["csv", "xlsx"])
        
        if uploaded_file:
            try:
                df, warnings = process_upload(uploaded_file, session)
                
                if warnings:
                    for w in warnings:
                        if w["level"] == "Error":
                            st.error(f"🛑 **{w['signal_id']}**: {w['msg']}")
                        else:
                            st.warning(f"⚠️ **{w['signal_id']}**: {w['msg']}")
                
                if not any(w["level"] == "Error" for w in warnings):
                    st.success("File validated.")
                    with st.expander("Preview Signal Data"):
                        st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button("🚀 Run Rules Engine & Save Analysis", type="primary"):
                        with st.spinner("Processing..."):
                            new_upload = Upload(client_id=confirmed_client.client_id, source_file=uploaded_file.name)
                            session.add(new_upload)
                            session.commit()
                            
                            prev_upload = session.query(Upload).filter(
                                Upload.client_id == confirmed_client.client_id,
                                Upload.upload_id != new_upload.upload_id
                            ).order_by(Upload.upload_id.desc()).first()
                            
                            signal_results = []
                            for signal_id in df.columns:
                                avg_val = float(df[signal_id].mean())
                                sig_config = get_signal_config(signal_id, config)
                                normalized = score_signal(avg_val, sig_config)
                                
                                trend_val = 0.0
                                if prev_upload:
                                    prev_res = session.query(SignalResult).filter_by(
                                        upload_id=prev_upload.upload_id, 
                                        signal_id=signal_id
                                    ).first()
                                    if prev_res:
                                        trend_val = calculate_trend(avg_val, prev_res.raw_value)
                                        
                                sr = SignalResult(
                                    upload_id=new_upload.upload_id,
                                    signal_id=signal_id,
                                    raw_value=avg_val,
                                    normalized_score=normalized,
                                    trend=trend_val,
                                    confidence=0.9
                                )
                                session.add(sr)
                                signal_results.append(sr)
                            
                            session.commit()
                            
                            index_res = IndexResult(upload_id=new_upload.upload_id)
                            weights = config.get("index_weights", {})
                            index_res.ssi = calculate_index([s for s in signal_results if s.signal_id in weights.get("SSI", {})], weights.get("SSI", {}))
                            index_res.fi = calculate_index([s for s in signal_results if s.signal_id in weights.get("FI", {})], weights.get("FI", {}))
                            index_res.ri = calculate_index([s for s in signal_results if s.signal_id in weights.get("RI", {})], weights.get("RI", {}))
                            index_res.qci = calculate_index([s for s in signal_results if s.signal_id in weights.get("QCI", {})], weights.get("QCI", {}))
                            index_res.bei = calculate_index([s for s in signal_results if s.signal_id in weights.get("BEI", {})], weights.get("BEI", {}))
                            indices = [index_res.ssi, index_res.fi, index_res.ri, index_res.qci, index_res.bei]
                            index_res.quality_maturity_score = sum(indices) / len(indices) if indices else 0.0
                            session.add(index_res)
                            session.commit()
                            
                            patterns = detect_patterns(signal_results, config.get("patterns", []), new_upload.upload_id)
                            for p in patterns: session.add(p)
                            session.commit()
                            alerts = generate_alerts(patterns, new_upload.upload_id)
                            for a in alerts: session.add(a)
                            session.commit()
                            
                            st.success(f"Analysis Complete for Batch {new_upload.upload_id}.")
                            st.balloons()
                else:
                    st.error("Engine Blocked: Correct critical data errors before processing.")
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "Signal Review":
    st.header("Signal Normalization & Trends")
    uploads = session.query(Upload).order_by(Upload.upload_id.desc()).all()
    if not uploads:
        st.info("No data available.")
    else:
        selected_upload_id = st.selectbox("Select Upload Batch", [u.upload_id for u in uploads])
        results = session.query(SignalResult).filter_by(upload_id=selected_upload_id).all()
        data = [{"Signal": session.query(Signal).filter_by(signal_id=r.signal_id).first().signal_name, "Domain": session.query(Signal).filter_by(signal_id=r.signal_id).first().domain, "Raw Value": r.raw_value, "Normalized Score": r.normalized_score, "Trend": r.trend} for r in results]
        df_res = pd.DataFrame(data)
        st.table(df_res)
        fig = px.bar(df_res, x='Signal', y='Normalized Score', color='Domain', title="Signal Performance")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Index Dashboard":
    st.header("Index Scoring Analysis")
    uploads = session.query(Upload).order_by(Upload.upload_id.desc()).all()
    if not uploads:
        st.info("No data available.")
    else:
        selected_upload_id = st.selectbox("Select Batch", [u.upload_id for u in uploads])
        idx = session.query(IndexResult).filter_by(upload_id=selected_upload_id).first()
        if idx:
            cols = st.columns(6)
            cols[0].metric("SSI", round(idx.ssi, 2))
            cols[1].metric("FI", round(idx.fi, 2))
            cols[2].metric("RI", round(idx.ri, 2))
            cols[3].metric("QCI", round(idx.qci, 2))
            cols[4].metric("BEI", round(idx.bei, 2))
            cols[5].metric("QMS", round(idx.quality_maturity_score, 2))
            
            quadrant = get_quadrant(idx.fi, idx.ri, config.get("quadrant_thresholds", {}))
            st.subheader(f"Strategic Placement: {quadrant}")
            
            current_upload = session.query(Upload).filter_by(upload_id=selected_upload_id).first()
            current_client = session.query(Client).filter_by(client_id=current_upload.client_id).first()
            
            # PDF Download
            patterns = session.query(PatternResult).filter_by(upload_id=selected_upload_id, active=True).all()
            alerts = session.query(Alert).filter_by(upload_id=selected_upload_id).all()
            pdf_bytes = generate_pdf_report(current_client.client_name, selected_upload_id, idx, patterns, alerts)
            st.download_button("Download Analysis Report (PDF)", data=pdf_bytes, file_name=f"VQP_Report_{selected_upload_id}.pdf", mime="application/pdf")

            # Radar Chart
            idx_data = pd.DataFrame({"Index": ["SSI", "FI", "RI", "QCI", "BEI"], "Score": [idx.ssi, idx.fi, idx.ri, idx.qci, idx.bei]})
            fig = px.line_polar(idx_data, r='Score', theta='Index', line_close=True, range_r=[0,1])
            st.plotly_chart(fig, use_container_width=True)

            # --- WHAT-IF SANDBOX ---
            st.divider()
            with st.expander("🛠️ Interactive 'What-If' Sandbox"):
                st.subheader("Simulate Signal Changes")
                batch_results = session.query(SignalResult).filter_by(upload_id=selected_upload_id).all()
                sandbox_values = {}
                cols_s = st.columns(len(batch_results))
                for i, r in enumerate(batch_results):
                    sig_conf = get_signal_config(r.signal_id, config)
                    is_pct = sig_conf.get("type") == "percentage"
                    sandbox_values[r.signal_id] = cols_s[i].slider(f"{r.signal_id}", 0.0, 1.0 if is_pct else 20.0, float(r.raw_value), 0.01 if is_pct else 1.0)
                
                sandbox_norm = [SignalResult(signal_id=sid, normalized_score=score_signal(val, get_signal_config(sid, config))) for sid, val in sandbox_values.items()]
                weights = config.get("index_weights", {})
                sim_ssi = calculate_index([s for s in sandbox_norm if s.signal_id in weights.get("SSI", {})], weights.get("SSI", {}))
                sim_fi = calculate_index([s for s in sandbox_norm if s.signal_id in weights.get("FI", {})], weights.get("FI", {}))
                sim_ri = calculate_index([s for s in sandbox_norm if s.signal_id in weights.get("RI", {})], weights.get("RI", {}))
                sim_qci = calculate_index([s for s in sandbox_norm if s.signal_id in weights.get("QCI", {})], weights.get("QCI", {}))
                sim_bei = calculate_index([s for s in sandbox_norm if s.signal_id in weights.get("BEI", {})], weights.get("BEI", {}))
                
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Sim SSI", round(sim_ssi, 2), delta=round(sim_ssi - idx.ssi, 2))
                m2.metric("Sim FI", round(sim_fi, 2), delta=round(sim_fi - idx.fi, 2))
                m3.metric("Sim RI", round(sim_ri, 2), delta=round(sim_ri - idx.ri, 2))
                m4.metric("Sim QCI", round(sim_qci, 2), delta=round(sim_qci - idx.qci, 2))
                m5.metric("Sim BEI", round(sim_bei, 2), delta=round(sim_bei - idx.bei, 2))
                m6.metric("Sim QMS", round((sim_ssi+sim_fi+sim_ri+sim_qci+sim_bei)/5, 2), delta=round(((sim_ssi+sim_fi+sim_ri+sim_qci+sim_bei)/5) - idx.quality_maturity_score, 2))

            # --- HISTORICAL TRENDS ---
            st.divider()
            st.subheader("📈 Historical Performance Trends")
            hist_query = f"SELECT u.upload_date, i.ssi, i.fi, i.ri, i.qci, i.bei FROM index_results i JOIN uploads u ON i.upload_id = u.upload_id WHERE u.client_id = {current_client.client_id} ORDER BY u.upload_date ASC"
            df_hist = pd.read_sql(hist_query, engine)
            if len(df_hist) > 1:
                df_long = df_hist.melt(id_vars=['upload_date'], var_name='Index Metric', value_name='Score')
                fig_t = px.line(df_long, x='upload_date', y='Score', color='Index Metric', title=f"Trend: {current_client.client_name}", range_y=[0, 1.1], markers=True)
                st.plotly_chart(fig_t, use_container_width=True)

elif page == "Pattern & Alerts":
    st.header("Pattern Detection & Alerts")
    uploads = session.query(Upload).order_by(Upload.upload_id.desc()).all()
    if uploads:
        selected_upload_id = st.selectbox("Select Batch", [u.upload_id for u in uploads])
        patterns = session.query(PatternResult).filter_by(upload_id=selected_upload_id, active=True).all()
        for p in patterns:
            st.warning(f"**Pattern Found: {p.pattern_id}** (Strength: {round(p.strength, 2)})\n\n{p.interpretation}")
        alerts = session.query(Alert).filter_by(upload_id=selected_upload_id).all()
        for a in alerts:
            st.markdown(f"**[{a.severity} Severity]** {a.message}")

elif page == "System Configuration":
    st.header("⚙️ System Rules Configuration")
    with open('config.json', 'r') as f: config_data = json.load(f)
    new_config_str = st.text_area("JSON Configuration Editor", value=json.dumps(config_data, indent=4), height=600)
    if st.button("💾 Save & Update Rules Engine"):
        try:
            with open('config.json', 'w') as f: f.write(new_config_str)
            st.success("Configuration updated successfully.")
        except Exception as e: st.error(f"Error saving: {e}")
