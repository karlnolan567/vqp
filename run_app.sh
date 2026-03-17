#!/bin/bash

# VQP Prototype - Dashboard Starter Script
echo "------------------------------------------------"
echo "🌐 Starting VQP Pharma Dashboard..."
echo "------------------------------------------------"

# Run streamlit via python3 module with headless and survey flags
python3 -m streamlit run app.py 
    --server.port 8501 
    --server.address 127.0.0.1 
    --browser.gatherUsageStats false 
    --server.headless true

# Note: If prompted for an email in some environments, 
# this headless flag should bypass it.
