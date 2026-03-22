# Claude Code Analytics Platform

An end-to-end analytics platform that processes Claude Code telemetry data and transforms raw event streams into actionable insights through an interactive dashboard, REST API, and anomaly detection.

Built as a technical assessment for the **Provectus Gen AI Internship Program**.

## Architecture

```
Raw JSONL Telemetry              SQLite Database              Interactive Dashboard
+-------------------+          +-----------------+          +-------------------+
| telemetry_logs    |  ingest  |  7 normalized   |  query   |  Streamlit +      |
| .jsonl (521 MB)   | -------> |  tables with    | -------> |  Plotly charts    |
| 454K events       |          |  indexes        |          |  8 pages          |
+-------------------+          +-----------------+          +-------------------+
                                       |
+-------------------+                  |                    +-------------------+
| employees.csv     |  load           |       query        |  FastAPI REST     |
| 100 engineers     | ------>         +-------------------> |  API (15+         |
+-------------------+                                      |  endpoints)       |
                                                           +-------------------+
```

**Pipeline stages:**

1. **Data Generation** , synthetic telemetry for 100 engineers over 60 days using the provided generator
2. **Ingestion** , parses nested JSONL batches, flattens events, validates data, batch-inserts into SQLite (~20s for 454K events)
3. **Storage** , 7 normalized tables (employees, sessions, api_requests, tool_decisions, tool_results, user_prompts, api_errors) with indexes for fast queries
4. **Analytics** , 20+ reusable query functions covering cost, usage trends, models, tools, errors, users, and anomaly detection
5. **Visualization** , 8-page Streamlit dashboard with Plotly charts, filters, and data tables
6. **API Access** , FastAPI endpoints for programmatic data retrieval (bonus)
7. **Anomaly Detection** , statistical methods to flag cost spikes (bonus)

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd claude-code-analytics

# Install dependencies
pip install -r requirements.txt

# Generate the dataset (100 users, 5000 sessions, 60 days)
python3 generate_fake_data.py --num-users 100 --num-sessions 5000 --days 60 --output-dir data

# Run the data ingestion pipeline
cd src
python3 ingest.py
cd ..

# Launch the dashboard
streamlit run app/dashboard.py
```

The dashboard will open at `http://localhost:8501`.

### Optional: REST API

```bash
pip install fastapi uvicorn
uvicorn api.api:app --reload
```

API docs available at `http://localhost:8000/docs`.

### Optional: Generate Presentation

```bash
pip install reportlab
python3 slides/generate_presentation.py
```

## Project Structure

```
claude-code-analytics/
├── generate_fake_data.py           # Telemetry data generator (provided)
├── data_README.md                  # Original dataset documentation
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── llm_usage_log.md                # AI tool usage documentation
├── .gitignore
│
├── data/                           # Generated data (gitignored)
│   ├── telemetry_logs.jsonl        # Raw telemetry (521 MB)
│   ├── employees.csv               # Employee directory
│   └── analytics.db                # SQLite database (97 MB)
│
├── src/                            # Core source code
│   ├── __init__.py
│   ├── database.py                 # Schema definition & connection management
│   ├── ingest.py                   # Data ingestion pipeline
│   └── analytics.py                # Analytics query engine (20+ functions)
│
├── app/                            # Dashboard
│   └── dashboard.py                # Streamlit interactive dashboard
│
├── api/                            # REST API (bonus)
│   ├── __init__.py
│   └── api.py                      # FastAPI endpoints
│
└── slides/                         # Presentation
    ├── generate_presentation.py    # PDF generator script
    └── insights_presentation.pdf   # 5-slide insights presentation
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| Overview | KPI cards, daily cost/user trends, cost by practice and model |
| Cost Analysis | Breakdown by model, practice, seniority level, top spenders |
| Usage Trends | Daily/weekly trends, hour-of-day patterns, day-of-week distribution |
| Model Analysis | Model efficiency (cost/token, speed), adoption over time |
| Tool Analysis | Usage frequency, success rates, tool preferences by practice |
| Error Analysis | Error types, trends, distribution by model |
| User Insights | Engagement scatter plots, environment breakdown, prompt analysis |
| Anomaly Detection | Statistical cost anomaly flagging (daily + per-user) |

## Key Findings

- **Total platform cost**: $6,001 across 60 days (~$100/day)
- **Opus models** account for 71% of cost despite only 42% of requests
- **Haiku** is 23x cheaper per request ($0.004 vs $0.093) making it ideal for simple tasks
- **70% of activity** happens during business hours (9-17 UTC)
- **Bash tool** has the lowest success rate (93%) among frequently used tools
- **Error rate is low** at 1.15%, with request aborts being the most common issue
- **All 100 engineers** actively used the platform, but usage varies 10x between users

## Tech Stack

- **Python 3.9+** , core language
- **SQLite** , lightweight embedded database with WAL mode
- **Streamlit** , interactive dashboard framework
- **Plotly** , rich interactive charts
- **FastAPI** , REST API endpoints (bonus)
- **ReportLab** , PDF presentation generation
- **pandas** , data manipulation

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /kpis` | Top-level KPI metrics |
| `GET /cost/by-model` | Cost breakdown by AI model |
| `GET /cost/by-practice` | Cost by engineering practice |
| `GET /cost/by-level` | Cost by seniority level |
| `GET /cost/top-users` | Top users by spending |
| `GET /usage/daily` | Daily usage metrics |
| `GET /usage/hourly` | Hourly distribution |
| `GET /models/efficiency` | Model performance comparison |
| `GET /tools/usage` | Tool usage summary |
| `GET /tools/success-rates` | Tool success/failure rates |
| `GET /errors/summary` | Error breakdown |
| `GET /users/engagement` | Per-user engagement metrics |
| `GET /anomalies/daily-cost` | Daily cost anomaly detection |
| `GET /anomalies/user-spending` | User spending anomalies |

## Dependencies

```
streamlit>=1.30.0
plotly>=5.18.0
pandas>=2.0.0
fastapi>=0.100.0      # optional, for API
uvicorn>=0.20.0       # optional, for API
reportlab>=4.0.0      # optional, for PDF generation
```
