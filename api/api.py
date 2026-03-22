"""
Claude Code Analytics - REST API

FastAPI endpoints for programmatic access to the processed telemetry data.
Run with: uvicorn api.api:app --reload

Bonus feature demonstrating API access capability.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI, Query

from analytics import (
    get_kpi_summary,
    get_cost_by_model,
    get_cost_by_practice,
    get_cost_by_level,
    get_cost_by_location,
    get_top_users_by_cost,
    get_daily_usage,
    get_hourly_distribution,
    get_model_efficiency,
    get_tool_usage_summary,
    get_tool_success_rates,
    get_error_summary,
    get_user_engagement,
    get_daily_cost_with_stats,
    get_user_cost_anomalies,
)

app = FastAPI(
    title="Claude Code Analytics API",
    description="REST API for accessing Claude Code telemetry insights",
    version="1.0.0",
)


@app.get("/")
def root():
    """API health check and endpoint listing."""
    return {
        "service": "Claude Code Analytics API",
        "version": "1.0.0",
        "endpoints": [
            "/kpis",
            "/cost/by-model",
            "/cost/by-practice",
            "/cost/by-level",
            "/cost/by-location",
            "/cost/top-users",
            "/usage/daily",
            "/usage/hourly",
            "/models/efficiency",
            "/tools/usage",
            "/tools/success-rates",
            "/errors/summary",
            "/users/engagement",
            "/anomalies/daily-cost",
            "/anomalies/user-spending",
        ],
    }


@app.get("/kpis")
def kpis():
    """Top-level KPI metrics."""
    return get_kpi_summary()


@app.get("/cost/by-model")
def cost_by_model():
    """Cost breakdown by AI model."""
    return get_cost_by_model().to_dict(orient="records")


@app.get("/cost/by-practice")
def cost_by_practice():
    """Cost breakdown by engineering practice."""
    return get_cost_by_practice().to_dict(orient="records")


@app.get("/cost/by-level")
def cost_by_level():
    """Cost breakdown by seniority level."""
    return get_cost_by_level().to_dict(orient="records")


@app.get("/cost/by-location")
def cost_by_location():
    """Cost breakdown by location."""
    return get_cost_by_location().to_dict(orient="records")


@app.get("/cost/top-users")
def top_users(limit: int = Query(default=15, ge=1, le=100)):
    """Top users by total cost."""
    return get_top_users_by_cost(limit).to_dict(orient="records")


@app.get("/usage/daily")
def daily_usage():
    """Daily aggregated usage metrics."""
    return get_daily_usage().to_dict(orient="records")


@app.get("/usage/hourly")
def hourly_usage():
    """Usage distribution by hour of day."""
    return get_hourly_distribution().to_dict(orient="records")


@app.get("/models/efficiency")
def model_efficiency():
    """Model comparison: cost per token, speed, usage."""
    return get_model_efficiency().to_dict(orient="records")


@app.get("/tools/usage")
def tool_usage():
    """Tool usage summary with acceptance rates."""
    return get_tool_usage_summary().to_dict(orient="records")


@app.get("/tools/success-rates")
def tool_success():
    """Tool execution success rates and durations."""
    return get_tool_success_rates().to_dict(orient="records")


@app.get("/errors/summary")
def errors():
    """Error summary by type and status code."""
    return get_error_summary().to_dict(orient="records")


@app.get("/users/engagement")
def user_engagement():
    """Per-user engagement metrics."""
    return get_user_engagement().to_dict(orient="records")


@app.get("/anomalies/daily-cost")
def daily_anomalies():
    """Daily cost anomaly detection results."""
    df = get_daily_cost_with_stats()
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


@app.get("/anomalies/user-spending")
def user_anomalies():
    """User-level spending anomalies."""
    return get_user_cost_anomalies().to_dict(orient="records")
