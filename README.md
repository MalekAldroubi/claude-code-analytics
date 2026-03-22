# Claude Code Analytics Platform

> Built as a technical assessment for the **Provectus Gen AI Internship Program**

## The Problem

Imagine 100 engineers using Claude Code (Anthropic's AI coding assistant) every day. Each session generates hundreds of telemetry events: API calls, tool executions, errors, prompts, and more. After 60 days, you're sitting on **521 MB of raw nested JSONL** and a CSV of employee metadata, with no way to answer basic questions like:

- Who's spending the most? Which teams?
- Which AI models are cost-efficient vs expensive?
- What tools fail the most, and why?
- When do developers actually code?
- Are there any abnormal cost spikes we should worry about?

This project turns that raw data into answers.

## What I Built

An end-to-end analytics platform that ingests raw telemetry, stores it in a structured database, runs 20+ analytical queries, and presents everything through an interactive dashboard and a REST API.

### Architecture

```
  telemetry_logs.jsonl (521 MB)        SQLite Database             Streamlit Dashboard
  employees.csv (100 users)            7 normalized tables         8 interactive pages
                                       with indexes
       |                                    |                           |
       |  [ingest.py]                       |  [analytics.py]           |  [dashboard.py]
       |  Parse nested JSON                 |  20+ query functions      |  Plotly charts
       |  Validate & clean                  |  Cost, trends, tools,     |  KPI cards
       |  Batch insert (5K rows)            |  models, errors,          |  Filters & tables
       v                                    v  anomaly detection        v
  +-----------+    load     +----------+   query   +------------------+
  | Raw Files | ---------> | SQLite   | --------> | Dashboard + API  |
  +-----------+            +----------+            +------------------+
                                                         |
                                                    [api.py]
                                                    15 REST endpoints
```

### Why These Design Decisions?

**Normalized tables instead of one flat table.** Each event type (api_request, tool_result, tool_decision, user_prompt, api_error) has different fields and different query patterns. Separating them means simpler, faster queries downstream.

**SQLite with WAL mode.** Lightweight, zero-config, and fast enough for this dataset. WAL (Write-Ahead Logging) allows the dashboard to read while the ingestion writes. Added a 64MB cache for better join performance.

**Batch inserts (5000 rows per flush).** Inserting row-by-row took ~120 seconds. Switching to `executemany` with batch flushing brought it down to ~20 seconds for 454K events.

**Indexes on the columns I filter most.** session_id, user_email, timestamp, tool_name, and model are the fields used in almost every dashboard query, so they get indexed.

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Setup (3 commands to a working dashboard)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the dataset and run the ingestion pipeline
python3 generate_fake_data.py --num-users 100 --num-sessions 5000 --days 60 --output-dir data
cd src && python3 ingest.py && cd ..

# 3. Launch the dashboard
streamlit run app/dashboard.py
```

The dashboard opens at `http://localhost:8501`.

### Optional: REST API

```bash
pip install fastapi uvicorn
uvicorn api.api:app --reload
```

Interactive API docs at `http://localhost:8000/docs`.

## Project Structure

```
claude-code-analytics/
├── generate_fake_data.py          # Telemetry data generator (provided)
├── data_README.md                 # Original dataset documentation
├── requirements.txt               # Python dependencies
├── llm_usage_log.md               # AI tool usage documentation
│
├── data/                          # Generated data (not in git, too large)
│   ├── telemetry_logs.jsonl       # Raw telemetry (521 MB)
│   ├── employees.csv              # Employee directory
│   └── analytics.db               # SQLite database (97 MB)
│
├── src/                           # Core pipeline
│   ├── database.py                # Schema definition, 7 tables, indexes
│   ├── ingest.py                  # Parses JSONL, validates, batch-loads
│   └── analytics.py               # 20+ query functions by domain
│
├── app/
│   └── dashboard.py               # 8-page Streamlit dashboard
│
├── api/
│   └── api.py                     # 15 FastAPI REST endpoints
│
└── slides/
    └── insights_presentation.pdf  # 5-slide findings presentation
```

## The Dashboard

Eight pages, each answering different stakeholder questions:

| Page | What It Answers |
|------|-----------------|
| **Overview** | How is the platform doing overall? KPIs, daily trends, cost distribution |
| **Cost Analysis** | Where is the money going? By model, team, seniority, individual users |
| **Usage Trends** | When do people code? Daily/weekly patterns, peak hours, weekday vs weekend |
| **Model Analysis** | Which models give the best value? Cost per token, speed, adoption trends |
| **Tool Analysis** | What tools do developers rely on? Success rates, durations, team preferences |
| **Error Analysis** | What's breaking? Error types, trends over time, which models fail most |
| **User Insights** | Who are the power users? Engagement patterns, IDE preferences, prompt behavior |
| **Anomaly Detection** | Should we be worried? Statistical cost spike detection at daily and per-user levels |

## Key Findings

Here's the story the data tells:

**Cost is dominated by model choice, not by usage volume.** Opus models account for 71% of the total $6,001 spend despite handling only 42% of requests. Haiku processes the most requests but costs just 3% of the total. This means the biggest cost lever isn't reducing usage, it's routing simple tasks to cheaper models.

**Developers are most active during business hours, but not exclusively.** 70% of API requests happen between 9-17 UTC, with a clear peak around mid-day. But there's meaningful activity at all hours, suggesting a distributed or flexible-hours team.

**Bash is the riskiest tool.** With a 93% success rate (vs 99%+ for file operations), shell command execution is where things go wrong most often. This could point to opportunities for better sandboxing or error recovery.

**The platform is healthy overall.** A 1.15% error rate is low, all 100 engineers are actively using Claude Code, and the anomaly detection flagged only 1 day out of 60 as unusual. No sustained cost drift was detected.

## Bonus Features

### Anomaly Detection
Two statistical approaches to flag unusual spending:

1. **Daily level:** 7-day rolling mean with a 2-sigma threshold. Any day where total cost exceeds the upper band gets flagged.
2. **User level:** Each user's daily spend is compared to their personal historical average + 2 standard deviations. Only users with 3+ active days are evaluated to avoid false positives.

### REST API
15 endpoints covering every analytics domain. Designed so that the same insights available in the dashboard can be consumed programmatically (e.g., for automated weekly reports or integration with other tools).

| Endpoint | Description |
|----------|-------------|
| `GET /kpis` | Top-level platform metrics |
| `GET /cost/by-model` | Cost breakdown by AI model |
| `GET /cost/by-practice` | Cost by engineering team |
| `GET /cost/by-level` | Cost by seniority level |
| `GET /cost/top-users` | Highest-spending users |
| `GET /usage/daily` | Daily usage metrics |
| `GET /usage/hourly` | Hour-of-day distribution |
| `GET /models/efficiency` | Cost per token, speed comparison |
| `GET /tools/usage` | Tool usage and acceptance rates |
| `GET /tools/success-rates` | Tool success/failure rates |
| `GET /errors/summary` | Error breakdown by type |
| `GET /users/engagement` | Per-user engagement metrics |
| `GET /anomalies/daily-cost` | Daily cost anomaly flags |
| `GET /anomalies/user-spending` | User spending anomalies |

## Tech Stack

| Tool | Why I Chose It |
|------|----------------|
| **Python 3.9+** | Standard for data engineering, great ecosystem |
| **SQLite** | Zero-config, embedded, fast enough for this scale, supports WAL mode for concurrent reads |
| **pandas** | Efficient data manipulation between SQL and visualization layers |
| **Streamlit** | Fastest path to a professional interactive dashboard without frontend overhead |
| **Plotly** | Rich, interactive charts that work natively with Streamlit |
| **FastAPI** | Modern, fast, auto-generates API documentation from type hints |
