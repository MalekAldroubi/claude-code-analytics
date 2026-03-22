"""
Analytics engine

Query functions that extract insights from the SQLite database. Used by the dashboard
"""

import sqlite3
import os
import pandas as pd

from database import get_connection


# Helper

def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SQL query and return a pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


# Overview / KPI Metrics

def get_kpi_summary() -> dict:
    """Return top-level KPIs for the overview dashboard."""
    conn = get_connection()
    c = conn.cursor()

    kpis = {}
    kpis["total_users"] = c.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    kpis["active_users"] = c.execute("SELECT COUNT(DISTINCT user_email) FROM sessions").fetchone()[0]
    kpis["total_sessions"] = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    kpis["total_api_requests"] = c.execute("SELECT COUNT(*) FROM api_requests").fetchone()[0]
    kpis["total_cost"] = c.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM api_requests").fetchone()[0]
    kpis["total_prompts"] = c.execute("SELECT COUNT(*) FROM user_prompts").fetchone()[0]
    kpis["total_errors"] = c.execute("SELECT COUNT(*) FROM api_errors").fetchone()[0]
    kpis["total_input_tokens"] = c.execute("SELECT COALESCE(SUM(input_tokens), 0) FROM api_requests").fetchone()[0]
    kpis["total_output_tokens"] = c.execute("SELECT COALESCE(SUM(output_tokens), 0) FROM api_requests").fetchone()[0]
    kpis["total_cache_read_tokens"] = c.execute("SELECT COALESCE(SUM(cache_read_tokens), 0) FROM api_requests").fetchone()[0]
    kpis["avg_cost_per_session"] = kpis["total_cost"] / max(kpis["total_sessions"], 1)
    kpis["avg_requests_per_session"] = kpis["total_api_requests"] / max(kpis["total_sessions"], 1)
    kpis["error_rate"] = kpis["total_errors"] / max(kpis["total_api_requests"], 1) * 100

    # Date range
    row = c.execute(
        "SELECT MIN(timestamp), MAX(timestamp) FROM api_requests"
    ).fetchone()
    kpis["date_from"] = row[0][:10] if row[0] else "N/A"
    kpis["date_to"] = row[1][:10] if row[1] else "N/A"

    conn.close()
    return kpis


# Cost Analysis

def get_cost_by_model() -> pd.DataFrame:
    """Total cost, request count, and avg cost per request by model."""
    return query_df("""
        SELECT
            model,
            COUNT(*) as request_count,
            SUM(cost_usd) as total_cost,
            AVG(cost_usd) as avg_cost,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            AVG(duration_ms) as avg_duration_ms
        FROM api_requests
        GROUP BY model
        ORDER BY total_cost DESC
    """)


def get_cost_by_practice() -> pd.DataFrame:
    """Cost breakdown by engineering practice."""
    return query_df("""
        SELECT
            e.practice,
            COUNT(DISTINCT a.user_email) as num_users,
            COUNT(*) as request_count,
            SUM(a.cost_usd) as total_cost,
            AVG(a.cost_usd) as avg_cost_per_request,
            SUM(a.cost_usd) / COUNT(DISTINCT a.user_email) as cost_per_user
        FROM api_requests a
        JOIN employees e ON a.user_email = e.email
        GROUP BY e.practice
        ORDER BY total_cost DESC
    """)


def get_cost_by_level() -> pd.DataFrame:
    """Cost breakdown by seniority level."""
    return query_df("""
        SELECT
            e.level,
            COUNT(DISTINCT a.user_email) as num_users,
            COUNT(*) as request_count,
            SUM(a.cost_usd) as total_cost,
            SUM(a.cost_usd) / COUNT(DISTINCT a.user_email) as cost_per_user
        FROM api_requests a
        JOIN employees e ON a.user_email = e.email
        GROUP BY e.level
        ORDER BY e.level
    """)


def get_cost_by_location() -> pd.DataFrame:
    """Cost breakdown by location."""
    return query_df("""
        SELECT
            e.location,
            COUNT(DISTINCT a.user_email) as num_users,
            SUM(a.cost_usd) as total_cost,
            SUM(a.cost_usd) / COUNT(DISTINCT a.user_email) as cost_per_user
        FROM api_requests a
        JOIN employees e ON a.user_email = e.email
        GROUP BY e.location
        ORDER BY total_cost DESC
    """)


def get_top_users_by_cost(limit: int = 15) -> pd.DataFrame:
    """Top N users by total cost."""
    return query_df("""
        SELECT
            a.user_email,
            e.full_name,
            e.practice,
            e.level,
            e.location,
            COUNT(*) as request_count,
            SUM(a.cost_usd) as total_cost,
            COUNT(DISTINCT a.session_id) as num_sessions
        FROM api_requests a
        JOIN employees e ON a.user_email = e.email
        GROUP BY a.user_email
        ORDER BY total_cost DESC
        LIMIT ?
    """, (limit,))


# Usage over time

def get_daily_usage() -> pd.DataFrame:
    """Daily aggregated usage metrics."""
    return query_df("""
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as api_requests,
            COUNT(DISTINCT session_id) as sessions,
            COUNT(DISTINCT user_email) as active_users,
            SUM(cost_usd) as total_cost,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens
        FROM api_requests
        GROUP BY DATE(timestamp)
        ORDER BY date
    """)


def get_weekly_usage() -> pd.DataFrame:
    """Weekly aggregated usage."""
    return query_df("""
        SELECT
            strftime('%Y-W%W', timestamp) as week,
            MIN(DATE(timestamp)) as week_start,
            COUNT(*) as api_requests,
            COUNT(DISTINCT session_id) as sessions,
            COUNT(DISTINCT user_email) as active_users,
            SUM(cost_usd) as total_cost
        FROM api_requests
        GROUP BY strftime('%Y-W%W', timestamp)
        ORDER BY week
    """)


def get_hourly_distribution() -> pd.DataFrame:
    """Distribution of API requests by hour of day."""
    return query_df("""
        SELECT
            CAST(strftime('%H', timestamp) AS INTEGER) as hour,
            COUNT(*) as request_count,
            SUM(cost_usd) as total_cost,
            COUNT(DISTINCT user_email) as unique_users
        FROM api_requests
        GROUP BY hour
        ORDER BY hour
    """)


def get_day_of_week_distribution() -> pd.DataFrame:
    """Usage distribution by day of week (0=Sunday, 6=Saturday)."""
    return query_df("""
        SELECT
            CAST(strftime('%w', timestamp) AS INTEGER) as day_of_week,
            COUNT(*) as request_count,
            SUM(cost_usd) as total_cost,
            COUNT(DISTINCT user_email) as unique_users
        FROM api_requests
        GROUP BY day_of_week
        ORDER BY day_of_week
    """)


# Model Analysis

def get_model_usage_over_time() -> pd.DataFrame:
    """Daily request count per model."""
    return query_df("""
        SELECT
            DATE(timestamp) as date,
            model,
            COUNT(*) as request_count,
            SUM(cost_usd) as total_cost
        FROM api_requests
        GROUP BY DATE(timestamp), model
        ORDER BY date, model
    """)


def get_model_efficiency() -> pd.DataFrame:
    """Compare models by cost-per-token and speed."""
    return query_df("""
        SELECT
            model,
            COUNT(*) as requests,
            AVG(duration_ms) as avg_duration_ms,
            AVG(output_tokens) as avg_output_tokens,
            AVG(cost_usd) as avg_cost,
            SUM(cost_usd) / NULLIF(SUM(output_tokens), 0) * 1000 as cost_per_1k_output,
            AVG(output_tokens * 1000.0 / NULLIF(duration_ms, 0)) as tokens_per_second
        FROM api_requests
        WHERE duration_ms > 0
        GROUP BY model
        ORDER BY avg_cost
    """)


# Tool Analysis

def get_tool_usage_summary() -> pd.DataFrame:
    """Summary of tool usage: decision counts, acceptance rate."""
    return query_df("""
        SELECT
            tool_name,
            COUNT(*) as total_decisions,
            SUM(CASE WHEN decision = 'accept' THEN 1 ELSE 0 END) as accepted,
            SUM(CASE WHEN decision = 'reject' THEN 1 ELSE 0 END) as rejected,
            ROUND(SUM(CASE WHEN decision = 'accept' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as accept_rate
        FROM tool_decisions
        GROUP BY tool_name
        ORDER BY total_decisions DESC
    """)


def get_tool_success_rates() -> pd.DataFrame:
    """Tool execution success/failure rates and durations."""
    return query_df("""
        SELECT
            tool_name,
            COUNT(*) as executions,
            SUM(success) as successes,
            COUNT(*) - SUM(success) as failures,
            ROUND(SUM(success) * 100.0 / COUNT(*), 1) as success_rate,
            AVG(duration_ms) as avg_duration_ms,
            MAX(duration_ms) as max_duration_ms
        FROM tool_results
        GROUP BY tool_name
        ORDER BY executions DESC
    """)


def get_tool_usage_by_practice() -> pd.DataFrame:
    """Which tools each practice uses most."""
    return query_df("""
        SELECT
            e.practice,
            tr.tool_name,
            COUNT(*) as usage_count
        FROM tool_results tr
        JOIN employees e ON tr.user_email = e.email
        GROUP BY e.practice, tr.tool_name
        ORDER BY e.practice, usage_count DESC
    """)


# Error Analysis

def get_error_summary() -> pd.DataFrame:
    """Error counts by type and status code."""
    return query_df("""
        SELECT
            error,
            status_code,
            COUNT(*) as error_count,
            AVG(attempt) as avg_retry_attempt
        FROM api_errors
        GROUP BY error, status_code
        ORDER BY error_count DESC
    """)


def get_error_trend() -> pd.DataFrame:
    """Daily error counts over time."""
    return query_df("""
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as error_count,
            status_code
        FROM api_errors
        GROUP BY DATE(timestamp), status_code
        ORDER BY date
    """)


def get_errors_by_model() -> pd.DataFrame:
    """Error distribution across models."""
    return query_df("""
        SELECT
            model,
            COUNT(*) as error_count,
            status_code
        FROM api_errors
        GROUP BY model, status_code
        ORDER BY error_count DESC
    """)


# Session Analysis

def get_session_stats() -> pd.DataFrame:
    """Per-session statistics: duration, requests, cost, tools used."""
    return query_df("""
        SELECT
            s.session_id,
            s.user_email,
            e.practice,
            e.level,
            s.terminal_type,
            s.os_type,
            s.started_at,
            s.ended_at,
            COALESCE(ar.request_count, 0) as api_requests,
            COALESCE(ar.total_cost, 0) as total_cost,
            COALESCE(ar.total_output_tokens, 0) as output_tokens,
            COALESCE(up.prompt_count, 0) as prompts,
            COALESCE(tr.tool_uses, 0) as tool_uses
        FROM sessions s
        JOIN employees e ON s.user_email = e.email
        LEFT JOIN (
            SELECT session_id,
                COUNT(*) as request_count,
                SUM(cost_usd) as total_cost,
                SUM(output_tokens) as total_output_tokens
            FROM api_requests GROUP BY session_id
        ) ar ON s.session_id = ar.session_id
        LEFT JOIN (
            SELECT session_id, COUNT(*) as prompt_count
            FROM user_prompts GROUP BY session_id
        ) up ON s.session_id = up.session_id
        LEFT JOIN (
            SELECT session_id, COUNT(*) as tool_uses
            FROM tool_results GROUP BY session_id
        ) tr ON s.session_id = tr.session_id
        ORDER BY ar.total_cost DESC
    """)


def get_session_duration_distribution() -> pd.DataFrame:
    """Distribution of session durations in minutes."""
    return query_df("""
        SELECT
            session_id,
            user_email,
            (julianday(ended_at) - julianday(started_at)) * 24 * 60 as duration_minutes
        FROM sessions
        WHERE ended_at > started_at
    """)


# User Engagement

def get_user_engagement() -> pd.DataFrame:
    """Per-user engagement metrics."""
    return query_df("""
        SELECT
            e.email,
            e.full_name,
            e.practice,
            e.level,
            e.location,
            COUNT(DISTINCT s.session_id) as sessions,
            COALESCE(SUM(ar.request_count), 0) as total_requests,
            COALESCE(SUM(ar.total_cost), 0) as total_cost,
            COALESCE(SUM(up.prompt_count), 0) as total_prompts,
            COUNT(DISTINCT DATE(s.started_at)) as active_days
        FROM employees e
        LEFT JOIN sessions s ON e.email = s.user_email
        LEFT JOIN (
            SELECT session_id, COUNT(*) as request_count, SUM(cost_usd) as total_cost
            FROM api_requests GROUP BY session_id
        ) ar ON s.session_id = ar.session_id
        LEFT JOIN (
            SELECT session_id, COUNT(*) as prompt_count
            FROM user_prompts GROUP BY session_id
        ) up ON s.session_id = up.session_id
        GROUP BY e.email
        ORDER BY total_cost DESC
    """)


def get_usage_by_terminal() -> pd.DataFrame:
    """Usage breakdown by terminal/IDE type."""
    return query_df("""
        SELECT
            s.terminal_type,
            COUNT(DISTINCT s.session_id) as sessions,
            COUNT(DISTINCT s.user_email) as unique_users,
            COALESCE(SUM(ar.total_cost), 0) as total_cost
        FROM sessions s
        LEFT JOIN (
            SELECT session_id, SUM(cost_usd) as total_cost
            FROM api_requests GROUP BY session_id
        ) ar ON s.session_id = ar.session_id
        GROUP BY s.terminal_type
        ORDER BY sessions DESC
    """)


def get_usage_by_os() -> pd.DataFrame:
    """Usage breakdown by operating system."""
    return query_df("""
        SELECT
            s.os_type,
            s.host_arch,
            COUNT(DISTINCT s.session_id) as sessions,
            COUNT(DISTINCT s.user_email) as unique_users
        FROM sessions s
        GROUP BY s.os_type, s.host_arch
        ORDER BY sessions DESC
    """)


# ---------------------------------------------------------------------------
# Prompt Analysis
# ---------------------------------------------------------------------------

def get_prompt_length_stats() -> pd.DataFrame:
    """Prompt length distribution stats by practice and level."""
    return query_df("""
        SELECT
            e.practice,
            e.level,
            COUNT(*) as prompt_count,
            AVG(p.prompt_length) as avg_length,
            MAX(p.prompt_length) as max_length,
            MIN(p.prompt_length) as min_length
        FROM user_prompts p
        JOIN employees e ON p.user_email = e.email
        GROUP BY e.practice, e.level
        ORDER BY e.practice, e.level
    """)


# Anomaly Detection (Outliers)

def get_daily_cost_with_stats() -> pd.DataFrame:
    """Daily cost with rolling average and standard deviation for anomaly detection."""
    df = get_daily_usage()
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["cost_7d_avg"] = df["total_cost"].rolling(window=7, min_periods=1).mean()
    df["cost_7d_std"] = df["total_cost"].rolling(window=7, min_periods=1).std().fillna(0)
    df["upper_bound"] = df["cost_7d_avg"] + 2 * df["cost_7d_std"]
    df["lower_bound"] = (df["cost_7d_avg"] - 2 * df["cost_7d_std"]).clip(lower=0)
    df["is_anomaly"] = (df["total_cost"] > df["upper_bound"]) | (df["total_cost"] < df["lower_bound"])

    return df


def get_user_cost_anomalies() -> pd.DataFrame:
    """Flag users whose daily spend deviates significantly from their own average."""
    return query_df("""
        WITH user_daily AS (
            SELECT
                user_email,
                DATE(timestamp) as date,
                SUM(cost_usd) as daily_cost
            FROM api_requests
            GROUP BY user_email, DATE(timestamp)
        ),
        user_stats AS (
            SELECT
                user_email,
                AVG(daily_cost) as avg_daily_cost,
                AVG(daily_cost) + 2 * COALESCE(
                    NULLIF(
                        SQRT(AVG(daily_cost * daily_cost) - AVG(daily_cost) * AVG(daily_cost)),
                        0
                    ), AVG(daily_cost) * 0.5
                ) as threshold
            FROM user_daily
            GROUP BY user_email
            HAVING COUNT(*) >= 3
        )
        SELECT
            ud.user_email,
            e.full_name,
            e.practice,
            ud.date,
            ud.daily_cost,
            us.avg_daily_cost,
            us.threshold
        FROM user_daily ud
        JOIN user_stats us ON ud.user_email = us.user_email
        JOIN employees e ON ud.user_email = e.email
        WHERE ud.daily_cost > us.threshold
        ORDER BY ud.daily_cost DESC
        LIMIT 50
    """)
