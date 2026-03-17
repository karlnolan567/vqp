# Virtual Quality Partners | QMS Design Prototype

A Python-based rules engine and professional dashboard for the pharmaceutical industry. This platform handles spreadsheet ingestion, advanced data validation, signal scoring, index calculation, pattern detection, and automated branded reporting.

## Project Overview

The VirtualQP platform transforms raw pharmaceutical data into actionable insights using a configuration-driven rules engine. It provides executive-level visibility into site performance, regulatory risks, and quality maturity.

### Key Features
- **Portfolio Overview:** Executive dashboard showing global metrics and risk distribution (FI vs RI).
- **Unified Data Ingestion:** Streamlined workflow for site enrollment and batch processing with instant validation.
- **Advanced Validation:** Automatic bound checks and Z-score outlier detection based on site history.
- **Rules Engine:** Configuration-driven scoring (SSI, FI, RI, QCI, BEI) with weighted averages and trend analysis.
- **Intelligence Layer:** Multi-signal pattern detection and predictive alerting.
- **Interactive Sandbox:** "What-If" analysis tool to simulate signal changes and their impact on QMS.
- **Branded Reporting:** Professional PDF generation with color-coded metrics and executive summaries.
- **System Configuration UI:** Admin interface to live-edit the rules engine thresholds and weights.

### Architecture
- **Frontend:** [Streamlit](https://streamlit.io/) with a professional Navy/Teal pharma-tech theme.
- **Backend Engine (`engine/`):**
  - `ingest.py`: Handles ingestion, mapping, and advanced outlier detection.
  - `signals.py`: Core scoring logic (positive/negative thresholds).
  - `indices.py`: Mathematical calculation of pharma indices and risk quadrants.
  - `patterns.py`: Intelligence-driven cluster detection.
- **Data Layer:** SQLite with SQLAlchemy ORM (`models.py`).
- **Reporting:** Branded PDF export via `fpdf` (`utils/reports.py`).

## Prototype Development Plan

The development followed a modular, configuration-driven strategy to maximize flexibility and industry compliance.

### Phase 1: Foundation & Branding (Weeks 1-2)
- **Technical Choice:** Streamlit + SQLAlchemy (SQLite).
- **Goal:** Establish core infrastructure and professional identity.
- **Key Outcomes:** Modular Python structure, relational data model, and Navy/Teal branding.

### Phase 2: The Rules Engine (Weeks 2-3)
- **Technical Choice:** JSON-based Configuration.
- **Goal:** Decouple business logic from application code.
- **Key Outcomes:** `config.json` rule definitions, normalized scoring engine, and index calculation logic.

### Phase 3: Intelligence & Visualization (Weeks 3-4)
- **Technical Choice:** Plotly + Z-Score Analytics.
- **Goal:** Provide longitudinal insights and predictive simulations.
- **Key Outcomes:** Historical trend charts, pattern detection clusters, and the interactive "What-If" Sandbox.

### Phase 4: Operations & Reporting (Week 5)
- **Technical Choice:** FPDF + Automated Test Suite.
- **Goal:** Ensure audit-readiness and operational reliability.
- **Key Outcomes:** Branded PDF report generation, System Configuration UI, and boundary-case unit tests.

## Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Convenience Scripts
- **Launch Application:** `./run_app.sh` (Starts Streamlit on `http://127.0.0.1:8501`)
- **Run Tests:** `./run_tests.sh` (Executes full suite with boundary cases)
- **Clear Data:** `./clear_data.sh` (Resets databases and re-seeds base signals)
- **Nuclear Reset:** `./reset_system.sh` (Full cleanup of DBs, cache, and active processes)

## Development & Testing

### Test Suite
The project includes a robust testing framework in `tests/`:
- `test_rules_engine.py`: Validates scoring logic, index calculation, and pattern detection across boundaries and edge cases.
- `test_ingestion.py`: Verifies file mapping and malformed data handling.

### Configuration
All business logic resides in `config.json`. This can be edited via the **System Configuration** page in the dashboard for real-time engine updates.

## Development Conventions
- **Configuration-First:** Thresholds and weights must remain in `config.json`.
- **Branding Consistency:** Adhere to the Navy (`#003366`) and Teal (`#00A8A8`) palette for all UI and report updates.
- **Data Integrity:** Ensure all calculations are persisted to allow for accurate historical trending and outlier detection.
- **Headless Execution:** Always run the server with `--server.headless true` in automated environments to bypass onboarding prompts.
