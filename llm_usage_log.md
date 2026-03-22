# LLM Usage Log

## Tools Used

- **Claude (Anthropic)**: Used throughout for code generation, schema design support, and documentation drafting
- **VS Code**: Primary development environment with Python extensions for linting and debugging

## My Approach

I used Claude as a development assistant, while keeping full ownership of architectural decisions and validation.

I defined the data model requirements, identified the key analytics questions, and guided the implementation step by step. Claude helped accelerate development, but I reviewed, tested, and refined every output before committing.

This reflects how I believe AI should be used in practice: the engineer drives the design and reasoning, while the LLM supports execution and iteration.

## Development Workflow

| Phase | My Role | Claude's Role |
|-------|---------|---------------|
| Data Exploration | Analyzed the JSONL structure, identified event types, mapped field relationships | N/A |
| Schema Design | Defined normalization strategy, chose SQLite with WAL mode, specified indexes based on expected query patterns | Generated initial CREATE TABLE statements from my specifications |
| Ingestion Pipeline | Designed the batch-insert approach, defined validation checks | Helped implement parsing logic and batch insert structure |
| Analytics Layer | Identified key business questions and defined metric logic (including anomaly detection) | Translated logic into SQL queries and pandas-compatible functions |
| Dashboard | Designed layout, selected metrics and visualizations | Generated Streamlit components and initial chart implementations |
| API Layer | Defined endpoint structure and expected responses | Helped scaffold FastAPI routes |

## Key Prompts & What I Learned

### 1. Data Modeling

**What I asked**:  
"I need a normalized schema for this telemetry data. The JSONL has nested batches with logEvents, each containing a message JSON with body, attributes, resource, and scope. I want separate tables for each event type (api_request, tool_decision, tool_result, user_prompt, api_error) plus a sessions table derived from session.id grouping and an employees table from the CSV. Use proper foreign keys and add indexes on session_id, user_email, timestamp, and tool_name since those are the columns I'll filter on most in the dashboard."

**What I validated**:  
- Verified schema consistency with raw data  
- Tested query performance using EXPLAIN QUERY PLAN  
- Ensured joins between api_requests and employees were efficient at scale  

---

### 2. Anomaly Detection Design

**What I asked**:  
"Implement two anomaly detection methods. First: daily cost anomalies using a 7-day rolling mean with 2 standard deviations as the threshold. Second: per-user anomalies comparing each user's daily spend to their own historical mean + 2 sigma. Only include users with at least 3 active days."

**What I validated**:  
- Checked that anomaly thresholds produced reasonable results  
- Ensured low-activity users were excluded to avoid noise  
- Verified output matched expected statistical behavior  

---

### 3. Dashboard Architecture

**What I asked**:  
"Build the dashboard with multiple pages including overview KPIs, cost analysis, usage trends, model comparison, tool usage, error analysis, and anomaly detection."

**What I validated**:  
- Cross-checked KPI values across different views  
- Ensured charts matched underlying SQL results  
- Verified filters and aggregations behaved correctly  

---

### 4. Performance Optimization

**What I asked**:  
"The ingestion is slow with row-by-row inserts. Refactor to use batch inserts with executemany and optimize SQLite settings."

**Result**:  
- Reduced ingestion time significantly  
- Applied WAL mode and caching to improve performance  
- Confirmed improvements by measuring execution time  

---

## Validation Process

Every piece of AI-generated code was validated before use:

1. Confirmed code runs without errors  
2. Verified row counts and aggregate values against raw data  
3. Checked for data consistency across tables  
4. Cross-validated dashboard outputs with direct SQL queries  
5. Ensured API responses match displayed metrics  

---

## Reflections

Using Claude helped speed up implementation and reduce time spent on repetitive coding and syntax lookups.

However, the most important part was maintaining control over design decisions and validating results carefully. In some cases, I adjusted or simplified the generated code to better fit the structure I had in mind.

For example, an initial suggestion was to use a single flat table for all events, but I chose a normalized schema because it better supports the different query patterns needed for analysis.

Overall, this approach allowed me to move faster while still understanding and verifying every part of the system.