# OBERON-301: Risk-Based Data Quality Monitor

A preventive risk scoring tool that identifies high-risk subjects and sites in clinical trials BEFORE issues become audit findings — using quantitative scoring across 6 risk dimensions and 10 clinical data sources.

Built by a Clinical Data Manager (CCDM®) with 17+ years of experience at J&J, Novartis, and BMS.

**No API keys. No AI costs. Pure statistical scoring. Instant results.**

---

## The Problem

Clinical Data Managers review all subjects equally. Subject 1 gets the same review time as Subject 50. But in reality, some subjects carry significantly more risk than others.

Risk-Based Monitoring (RBM) is an ICH E6 R2 mandate — yet most CROs still implement it through subjective assessment, spreadsheet trackers, and gut instinct. There is no quantitative, data-driven way to prioritize review effort across subjects and sites.

**The result:** CDMs waste hours reviewing clean subjects while high-risk subjects with unaddressed safety signals, aged queries, and protocol deviations go undetected until audit.

## The Solution

This tool calculates a **Risk Score (0–100)** for every subject and site by analyzing data across **6 dimensions** and **10 clinical data sources** — transforming risk-based monitoring from subjective judgment to data-driven decision making.

```
┌──────────────────────────────────────────┐
│       Upload 10 CSV Data Sources         │
│                                          │
│   Core CRF (7):        Operational (3):  │
│   Demographics          Query Detail     │
│   Medical History       Protocol Devs    │
│   Concomitant Meds      Visit Tracking   │
│   Adverse Events                         │
│   Lab Data                               │
│   Vital Signs                            │
│   Disposition                            │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│         6-Dimension Risk Scoring         │
│                                          │
│   D1: Data Completeness        (0-20)    │
│   D2: Query Rate & Aging       (0-20)    │
│   D3: Temporal & Visit Anomaly (0-15)    │
│   D4: Safety Signals           (0-20)    │
│   D5: Site Risk Aggregation    (0-15)    │
│   D6: Protocol Deviations      (0-10)    │
│                                          │
│           Total: 0-100                   │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│          Risk Dashboard                  │
│                                          │
│   Summary Cards (risk distribution)      │
│   Operational Metrics (queries/PDs/      │
│     visits)                              │
│   Dimension Averages (study-level)       │
│   Site Risk Ranking                      │
│   Subject Risk Table (sortable/          │
│     filterable)                          │
│   Subject Detail View (per-dimension     │
│     breakdown)                           │
│   CSV Export                             │
└──────────────────────────────────────────┘
```

## The 6 Risk Dimensions

| Dimension | What It Measures | Max | Data Sources Used |
|-----------|-----------------|-----|-------------------|
| **D1: Data Completeness** | Missing/blank fields across all 10 forms | 20 | All 10 datasets |
| **D2: Query Rate & Aging** | Query volume vs study average, open queries, aged queries (>14 days) | 20 | Query Detail Report |
| **D3: Temporal & Visit Anomaly** | Date inconsistencies, missed visits, visit window violations | 15 | Demographics, AE, MH, Visit Tracking |
| **D4: Safety Signals** | Lab trending without AE, vital sign changes without documentation | 20 | Lab Data, Vital Signs, Adverse Events |
| **D5: Site Risk** | Site-level query rates, AE under-reporting, PD concentration, discontinuation rates | 15 | All datasets aggregated by site |
| **D6: Protocol Deviations** | Eligibility violations, formal PD records, CAPA status, disposition contradictions | 10 | Demographics, MH, Protocol Deviations, Disposition, AE |

## Key Results

| Metric | Value |
|--------|-------|
| Data sources analyzed | 10 |
| Subjects scored | 62 |
| Risk dimensions | 6 |
| Processing time | < 3 seconds |
| API cost per run | $0 |
| High-risk subjects correctly identified | All planted error subjects scored HIGH or CRITICAL |

## What This Tool Catches

**Traditional approach (subjective):**
> "Site 3 seems to have more issues than other sites. Let's keep an eye on it."

**This tool (quantitative):**
> "Site SITE-1003 scores 42/100 average risk — driven by 15% missing data rate, AE reporting at 0.6x study average, 3 major protocol deviations, and 9 open queries. Top risk subjects: OB1132 (score 78), OB1122 (score 72). Recommend immediate targeted review."

### Specific Examples from Test Data

| Subject | Risk Score | Category | Primary Risk Drivers |
|---------|-----------|----------|---------------------|
| OB1140 | 78 | CRITICAL | 10 queries (4.2x avg), hospitalization AE marked non-serious |
| OB1132 | 75 | CRITICAL | ALT trending 27→180 U/L (no AE), 8 queries |
| OB1122 | 72 | CRITICAL | BP >160/100 all visits (no AE, no med), no antihypertensive |
| OB1176 | 68 | HIGH | Fatal MI but disposition "Completed", 6 queries |
| OB1162 | 65 | HIGH | Hepatic impairment (exclusion violation), 4 PDs, 7 queries |
| OB1175 | 58 | HIGH | Missed visit, 5 protocol deviations, open CAPA |
| OB1165 | 55 | HIGH | 4 aged open queries, 2 late visits (14 days outside window) |
| OB1134 | 52 | HIGH | +14kg weight gain (no AE), visit window violation |

## Dashboard Features

### Summary Cards
Total subjects, risk category breakdown (Critical/High/Medium/Low), average and max risk scores — all at a glance.

### Operational Metrics
Three dedicated panels showing study-wide health indicators:
- **Query Metrics** — Total queries, open queries, average per subject
- **Protocol Deviations** — Total PDs, major PDs, open CAPAs requiring resolution
- **Visit Compliance** — Total visits tracked, missed visits, window violations

### Dimension Averages
Study-level bar chart showing which risk dimensions are driving the most risk across the entire study population. Identifies systemic issues (e.g., if D4 Safety is consistently high, the study may have an AE under-reporting problem).

### Site Risk Ranking
Site-by-site comparison with average and maximum risk scores. Color-coded to highlight sites requiring attention. Incorporates query volume, AE reporting rates, PD concentration, and discontinuation rates.

### Subject Risk Table
Sortable, filterable table with all subjects. Filter by risk category or site. Sort by total score or individual dimension. Click any subject for detailed breakdown.

### Subject Detail View
Click any subject to see a per-dimension breakdown with specific findings — exactly what's driving their risk score and why, with actionable detail for CDM follow-up.

### CSV Export
Download complete risk scores with dimension breakdowns and detail notes for offline analysis, TMF filing, or integration with existing CDM workflows.

## Companion Tool

This is the **preventive** complement to the [OBERON-301 Cross-Form Clinical Data Review Assistant](https://github.com/nareshparlapalli/OBERON-301-Clinical-Review), which provides **corrective** error detection using rule-based checks + LLM-powered clinical reasoning.

| | Cross-Form Review | Risk Monitor (This Tool) |
|---|---|---|
| **Purpose** | Find existing errors | Predict where errors will occur |
| **Approach** | Corrective | Preventive |
| **Technology** | Rule engine + LLM (GPT-4o) | Pure statistical scoring |
| **Data sources** | 7 CRF domains | 10 (7 CRF + 3 operational) |
| **Cost per run** | ~$1.50 (API) | $0 |
| **Speed** | 5-10 minutes | < 3 seconds |
| **Output** | Flagged errors + query text | Risk scores + priority list |
| **Best for** | Data review, pre-lock QC | Ongoing monitoring, RBM |

**Together:** Review everything → Review intelligently based on risk.

## Scoring Methodology

### How Risk Scores Are Calculated

Each subject receives a score from 0–100 based on weighted findings across 6 dimensions:

**D1 — Data Completeness (0–20):**
Percentage of missing/blank fields across all 10 data sources. Thresholds: >15% = 20 pts, 10–15% = 12, 5–10% = 5, <5% = 0.

**D2 — Query Rate & Aging (0–20):**
Uses real query data. Scores based on: query volume vs study average (>3x avg = high risk), number of open queries (≥3 = high risk), aged queries >14 days (prolonged site non-response), and answered-but-unclosed queries.

**D3 — Temporal & Visit Anomaly (0–15):**
Combines date validation (consent after screening, AE before consent, MH after screening) with visit tracking analysis (missed visits, visits outside permitted window, irregular spacing patterns).

**D4 — Safety Signals (0–20):**
Detects unaddressed safety findings: ALT/AST trending >2x ULN without hepatic AE, hemoglobin dropping >3 g/dL without anemia AE, BP consistently >160/100 without hypertension AE or medication, weight changes >7kg between visits, abnormal labs with zero AE reporting.

**D5 — Site Risk (0–15):**
Aggregates site-level indicators: query rate vs study average, open/aged query concentration, AE reporting rate (low = under-reporting risk), major PD concentration at site, and discontinuation rate.

**D6 — Protocol Deviations (0–10):**
Combines rule-based checks (age criteria, exclusion terms) with formal PD records (major vs minor classification, CAPA status), fatal AE vs disposition contradictions, and early study completion.

### Risk Categories

| Score | Category | Action |
|-------|----------|--------|
| 0–20 | LOW | Standard review |
| 21–40 | MEDIUM | Priority review |
| 41–60 | HIGH | Immediate review |
| 61–100 | CRITICAL | Escalate to lead CDM |

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Scoring Engine:** Pandas, NumPy (pure statistical — no ML/AI dependencies)
- **Frontend:** HTML, CSS, JavaScript
- **External APIs:** None required
- **Standards Referenced:** ICH E6 R2 (Risk-Based Monitoring), ICH-GCP, CDISC

## Project Structure

```
OBERON-301-Risk-Monitor/
├── app.py                        # FastAPI backend
├── risk_scoring.py               # Core scoring engine (6 dimensions)
├── requirements.txt              # Python dependencies
├── START_APP.bat                 # One-click Windows launcher
├── .gitignore
├── templates/
│   └── index.html                # Dashboard UI
└── data/
    ├── Demographics.csv          # Core CRF
    ├── Medical_History.csv       # Core CRF
    ├── Concomitant_Meds.csv      # Core CRF
    ├── Adverse_Events.csv        # Core CRF
    ├── Lab_Data.csv              # Core CRF
    ├── Vital_Signs.csv           # Core CRF
    ├── Disposition.csv           # Core CRF
    ├── Query_Detail.csv          # Operational
    ├── Protocol_Deviations.csv   # Operational
    └── Visit_Tracking.csv        # Operational
```

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- No API keys needed

### Quick Start (Windows)
```bash
git clone https://github.com/nareshparlapalli/OBERON-301-Risk-Monitor.git
cd OBERON-301-Risk-Monitor

# Option 1: Double-click START_APP.bat

# Option 2: Manual setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

Open browser → **http://localhost:8001**

### Quick Start (Mac/Linux)
```bash
git clone https://github.com/nareshparlapalli/OBERON-301-Risk-Monitor.git
cd OBERON-301-Risk-Monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

### Usage
1. Upload all 10 CSV files (7 Core CRF + 3 Operational)
2. Click **"Run Risk Analysis"**
3. Review dashboard: summary → operational metrics → dimensions → sites → subjects
4. Click any Subject ID for detailed dimension breakdown
5. Filter by risk category or site
6. Export results to CSV

## Clinical Validation

Tested against a synthetic dataset of 62 subjects with planted cross-form errors, high-query subjects, protocol deviations, missed visits, and safety signals. All subjects with planted issues scored in the HIGH or CRITICAL risk categories.

**Important:** This tool is a risk prioritization assistant. It does not replace clinical judgment — it directs CDM attention where it matters most. For production deployment, appropriate validation (IQ/OQ/PQ), SOPs, and audit trail requirements would apply per ICH E6 R2 and 21 CFR Part 11.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` not recognized | Reinstall Python with "Add to PATH" checked |
| `venv\Scripts\activate` error | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` in PowerShell |
| Port 8001 in use | Change port: `python -m uvicorn app:app --port 8002` |
| Internal Server Error | Check Command Prompt for the Python error message |

## About

Built by **Naresh Parlapalli, CCDM®** — 17+ years in Clinical Data Management at J&J, Novartis, BMS, IQVIA, and Syneos Health. This tool demonstrates how quantitative risk scoring transforms RBM from subjective assessment to data-driven decision making — using real CDM domain knowledge to define what "risk" actually means in clinical trial operations.

Contact: naresh.0705@gmail.com | +91 7829100707

## License

This project is for demonstration and educational purposes.
