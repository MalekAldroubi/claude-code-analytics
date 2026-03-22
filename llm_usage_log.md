# LLM Usage Log

## Tools Used

- **Claude (Anthropic)**: Used for code generation, schema design, and documentation help
- **VS Code**: Development environment with Python extensions

## My Approach

Before starting, I read through Anthropic's prompt engineering documentation to understand how to get the best results from Claude. The main takeaways I applied were: using XML-style tags to structure my requests, being very specific about what I want (and what I don't want), and asking Claude to think step by step for complex tasks.

I tried to treat Claude like a coding partner rather than a magic box. I would figure out what I needed first, then write a detailed prompt explaining the goal, the data, the constraints, and the expected output. This worked much better than vague requests.

## Development Workflow

| Phase | What I Did | What Claude Helped With |
|-------|------------|------------------------|
| Data Exploration | Read through the JSONL structure, identified the 5 event types, understood how events relate to each other | N/A, this was manual exploration |
| Schema Design | Decided on normalized tables, picked which columns to index | Generated the SQL CREATE TABLE statements from my spec |
| Ingestion Pipeline | Planned the batch-insert approach after the first version was too slow | Wrote the parsing and insert logic |
| Analytics Layer | Listed the business questions I wanted to answer | Turned my questions into SQL queries and pandas functions |
| Dashboard | Picked which charts to use for each metric | Built the Streamlit pages and Plotly charts |
| API | Decided on the endpoint structure | Scaffolded the FastAPI routes |

## Prompt Engineering Approach

Following Anthropic's recommendations, I structured my prompts with:

- **`<role>`** to set context for what kind of task Claude is doing
- **`<context>`** to provide all the relevant background information
- **`<task>`** with numbered steps for complex requests
- **`<constraints>`** to prevent common mistakes and specify what I don't want
- **`<output_format>`** to define exactly what the deliverable should look like

I found that the more specific I was, the less I had to fix afterwards. Below are some examples.

## Key Prompts

### 1. Schema Design

This was the first and most important prompt. I spent time understanding the data before writing it.

**Prompt:**

```
<role>
You are a data engineer designing a database schema for a telemetry analytics platform.
</role>

<context>
I have a JSONL file (521 MB) containing Claude Code telemetry data. Each line is a
CloudWatch-style log batch with this structure:
- Top level: messageType, owner, logGroup, logStream, logEvents[]
- Each logEvent contains a "message" field which is a JSON string
- The message JSON has: body (event type), attributes (event-specific fields),
  resource (host/user environment), scope (instrumentation metadata)

There are 5 event types identified by the "body" field:
- claude_code.api_request: model calls with tokens, cost, duration
- claude_code.tool_decision: accept/reject decisions for tool usage
- claude_code.tool_result: execution outcomes with success/failure
- claude_code.user_prompt: user messages with prompt length
- claude_code.api_error: failures with status codes and error messages

I also have an employees.csv with: email, full_name, practice, level, location.
</context>

<task>
Design a normalized SQLite schema with these requirements:
1. Separate table for each event type (not a flat table, because query patterns differ)
2. A sessions table derived from grouping by session.id across all events
3. An employees table loaded from the CSV
4. Foreign keys linking sessions to employees via user_email
5. Indexes on: session_id, user_email, timestamp, tool_name, model
   (these are the columns I will filter on most in dashboard queries)
6. Use appropriate types: INTEGER for tokens, REAL for cost, TEXT for timestamps
</task>

<constraints>
- Do not create a single flat table for all events
- Do not use an ORM, use raw SQL with sqlite3
- Include PRAGMA optimizations (WAL mode, cache size)
</constraints>

<output_format>
A Python module (database.py) with:
- get_connection() function with PRAGMA settings
- create_schema() function with all CREATE TABLE and CREATE INDEX statements
</output_format>
```

**How I checked it:** Verified the table structure matches the raw data fields. Ran test queries to make sure JOINs between tables worked. Confirmed zero orphaned records after ingestion.

---

### 2. Anomaly Detection

I wanted to add this as a bonus feature. I had to think about what "anomaly" means in this context before prompting.

**Prompt:**

```
<role>
You are a data analyst implementing anomaly detection for a cost monitoring system.
</role>

<context>
I have daily cost data from an api_requests table over 60 days. I also have
per-user daily cost breakdowns. I need to flag unusual cost patterns at two levels.
</context>

<task>
Implement two anomaly detection methods:

Method 1 - Daily cost anomalies:
- Compute a 7-day rolling mean of total daily cost
- Compute a 7-day rolling standard deviation
- Flag any day where actual cost falls outside mean +/- 2 standard deviations
- Return the full dataframe with: date, total_cost, rolling_avg, upper_bound,
  lower_bound, is_anomaly

Method 2 - Per-user spending anomalies:
- For each user, compute their personal average daily cost and standard deviation
- Flag user-days where spend exceeds their own mean + 2 sigma
- Only include users with at least 3 active days (to avoid false positives
  from low sample sizes)
- Return: user_email, full_name, practice, date, daily_cost, avg_daily_cost, threshold

Think through this step by step before writing the code.
</task>

<constraints>
- Method 1 should use pandas rolling() for clean implementation
- Method 2 should be a single SQL query using CTEs (WITH clauses), not Python loops
- Both should be functions in analytics.py that return DataFrames
- Handle edge cases: fillna(0) for early days with insufficient rolling window
</constraints>
```

**How I checked it:** Made sure the threshold flagged a reasonable number of days (1 out of 60). Verified that users with fewer than 3 active days were excluded. Looked at the flagged anomalies to confirm they were actual cost spikes, not noise.

---

### 3. Dashboard

For the dashboard, I learned that specifying exact chart types matters a lot. My first attempt was vague ("build a dashboard for this data") and the result was generic. The version below worked much better.

**Prompt:**

```
<role>
You are a frontend data engineer building an analytics dashboard.
</role>

<context>
I have an analytics.py module with 20+ query functions returning pandas DataFrames.
The data covers Claude Code usage: costs, models, tools, errors, sessions, users.
The audience is engineering managers who need quick insights.
</context>

<task>
Build a multi-page Streamlit dashboard with these pages and chart types:

1. Overview: 8 KPI cards + area chart (daily cost) + bar (active users) +
   bar (cost by practice) + donut (cost by model)

2. Cost Analysis: 4 tabs (by model, by practice, by level, top users).
   Bar charts with values displayed. Data tables below each.

3. Usage Trends: Line chart with metric dropdown + 7-day rolling average overlay.
   Hour-of-day bar chart with business hours (9-17) highlighted in blue.
   Day-of-week bars with weekdays green, weekends red.

4. Model Analysis: Bar charts for cost-per-1K-tokens and tokens-per-second.
   Bubble scatter (x=duration, y=cost, size=requests, color=model).
   Stacked area chart for model adoption over time.

5. Tool Analysis: Bar chart colored by acceptance rate.
   Heatmap of tool usage by practice.

6. Error Analysis: Horizontal bars for error types by status code.
   Area chart for daily error count.

7. User Insights: Scatter plots (sessions vs cost, active days vs cost).
   Pie charts for terminal/IDE and OS.

8. Anomaly Detection: Line with confidence band, rolling average as dashed,
   anomaly points as red X markers.
</task>

<constraints>
- Dark theme (background #0e1117, cards #1a1f2e)
- Plotly for all charts, not matplotlib
- Consistent colors across pages
- Transparent chart backgrounds
</constraints>
```

**How I checked it:** Opened every page and made sure charts load. Cross-checked that the total cost on the Overview page matches the sum on the Cost Analysis page. Verified filters and dropdowns work.

---

### 4. Performance Fix

This one was short because the problem was clear.

**Prompt:**

```
<task>
The ingestion is too slow with row-by-row inserts (~120 seconds for 454K events).
Refactor to batch inserts: accumulate rows in lists, flush every 5000 rows with
executemany(), enable WAL mode, set cache_size to 64MB.
</task>
```

**Result:** Went from ~120s to ~20s.

---

## Validation

For every piece of generated code, I checked:

1. Does it run without errors?
2. Do the row counts match what the data generator reports?
3. Do the numbers on the dashboard match direct SQL queries?
4. Are there any orphaned or missing records?

---

## What I Learned

- Structured prompts with XML tags consistently gave better results than freeform requests
- Being specific about what I don't want (constraints) was just as important as what I do want
- The first version of most outputs needed some adjustment, but having a solid starting point saved a lot of time
- Understanding the data before prompting was essential. I couldn't have written these prompts without first exploring the JSONL structure manually
- AI is a great accelerator, but I still needed to understand what I was building to validate the output
