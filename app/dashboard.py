"""
Claude Code Analytics Dashboard

Interactive Streamlit dashboard for exploring Claude Code telemetry data.
Ran with: streamlit 
run app/dashboard.py
"""

import sys
import os

# Add src/ to path so we can import analytics and database modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from analytics import (
    get_kpi_summary,
    get_cost_by_model,
    get_cost_by_practice,
    get_cost_by_level,
    get_cost_by_location,
    get_top_users_by_cost,
    get_daily_usage,
    get_weekly_usage,
    get_hourly_distribution,
    get_day_of_week_distribution,
    get_model_usage_over_time,
    get_model_efficiency,
    get_tool_usage_summary,
    get_tool_success_rates,
    get_tool_usage_by_practice,
    get_error_summary,
    get_error_trend,
    get_errors_by_model,
    get_session_stats,
    get_user_engagement,
    get_usage_by_terminal,
    get_usage_by_os,
    get_prompt_length_stats,
    get_daily_cost_with_stats,
    get_user_cost_anomalies,
)

# Page Config & Styling

st.set_page_config(
    page_title="Claude Code Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1f2e 0%, #151922 100%);
        border: 1px solid #2a2f3e;
        border-radius: 12px;
        padding: 16px 20px;
    }

    div[data-testid="stMetric"] label {
        color: #8b95a5 !important;
        font-size: 0.85rem !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e8ecf1 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #151922;
        border-right: 1px solid #2a2f3e;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1a1f2e;
        border-radius: 8px;
        padding: 8px 16px;
        color: #8b95a5;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }

    /* Headers */
    h1, h2, h3 {
        color: #e8ecf1 !important;
    }

    /* Divider */
    hr {
        border-color: #2a2f3e;
    }
</style>
""", unsafe_allow_html=True)


# Color palette
COLORS = {
    "primary": "#2563eb",
    "secondary": "#7c3aed",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#06b6d4",
}

MODEL_COLORS = {
    "claude-haiku-4-5-20251001": "#10b981",
    "claude-opus-4-6": "#7c3aed",
    "claude-opus-4-5-20251101": "#2563eb",
    "claude-sonnet-4-5-20250929": "#f59e0b",
    "claude-sonnet-4-6": "#ef4444",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b95a5", family="system-ui, -apple-system, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#1e2433", zerolinecolor="#1e2433"),
    yaxis=dict(gridcolor="#1e2433", zerolinecolor="#1e2433"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="#1a1f2e", font_color="#e8ecf1"),
)


def apply_layout(fig, **kwargs):
    """Apply consistent styling to a Plotly figure."""
    layout = {**PLOTLY_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig


# Sidebar

with st.sidebar:
    st.markdown("## Claude Code Analytics")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "🏠 Overview",
            "💰 Cost Analysis",
            "📈 Usage Trends",
            "🤖 Model Analysis",
            "🔧 Tool Analysis",
            "❌ Error Analysis",
            "👥 User Insights",
            "🔍 Anomaly Detection",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        "<div style='color: #555; font-size: 0.8rem;'>"
        "Built for Provectus Gen AI Internship<br>"
        "Data: Dec 2025 - Jan 2026"
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Page: Overview

if page == "🏠 Overview":
    st.title("Claude Code Analytics Platform")
    st.markdown("End-to-end telemetry analysis for Claude Code developer sessions")
    st.markdown("---")

    kpis = get_kpi_summary()

    # Row 1: Top-level KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Users", f"{kpis['active_users']}")
    c2.metric("Total Sessions", f"{kpis['total_sessions']:,}")
    c3.metric("Total API Cost", f"${kpis['total_cost']:,.2f}")
    c4.metric("API Requests", f"{kpis['total_api_requests']:,}")

    # Row 2
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Avg Cost/Session", f"${kpis['avg_cost_per_session']:.2f}")
    c6.metric("Error Rate", f"{kpis['error_rate']:.2f}%")
    c7.metric("Total Prompts", f"{kpis['total_prompts']:,}")
    c8.metric("Date Range", f"{kpis['date_from']} to {kpis['date_to']}")

    st.markdown("---")

    # Daily usage chart
    daily = get_daily_usage()
    daily["date"] = pd.to_datetime(daily["date"])

    col_left, col_right = st.columns(2)

    with col_left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["date"], y=daily["total_cost"],
            fill="tozeroy", name="Daily Cost",
            line=dict(color=COLORS["primary"], width=2),
            fillcolor="rgba(37, 99, 235, 0.15)",
        ))
        apply_layout(fig, title="Daily API Cost ($)", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily["date"], y=daily["active_users"],
            name="Active Users", marker_color=COLORS["success"],
            opacity=0.8,
        ))
        apply_layout(fig, title="Daily Active Users", height=350)
        st.plotly_chart(fig, use_container_width=True)

    # Cost by practice and model side by side
    col_left, col_right = st.columns(2)

    with col_left:
        cost_practice = get_cost_by_practice()
        fig = px.bar(
            cost_practice, x="practice", y="total_cost",
            color="practice", text_auto="$.2f",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        apply_layout(fig, title="Total Cost by Practice", showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        cost_model = get_cost_by_model()
        fig = px.pie(
            cost_model, values="total_cost", names="model",
            color="model", color_discrete_map=MODEL_COLORS,
            hole=0.4,
        )
        apply_layout(fig, title="Cost Distribution by Model", height=350)
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: Cost Analysis

elif page == "💰 Cost Analysis":
    st.title("💰 Cost Analysis")
    st.markdown("Understanding where Claude Code spending goes")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["By Model", "By Practice", "By Level", "Top Users"])

    with tab1:
        df = get_cost_by_model()
        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df, x="model", y="total_cost", color="model",
                color_discrete_map=MODEL_COLORS,
                text_auto="$.0f",
            )
            apply_layout(fig, title="Total Cost by Model", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                df, x="model", y="avg_cost", color="model",
                color_discrete_map=MODEL_COLORS,
                text_auto="$.4f",
            )
            apply_layout(fig, title="Average Cost per Request", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df.rename(columns={
                "model": "Model", "request_count": "Requests",
                "total_cost": "Total Cost ($)", "avg_cost": "Avg Cost ($)",
                "total_input_tokens": "Input Tokens", "total_output_tokens": "Output Tokens",
                "avg_duration_ms": "Avg Duration (ms)",
            }).style.format({
                "Total Cost ($)": "${:,.2f}",
                "Avg Cost ($)": "${:,.4f}",
                "Input Tokens": "{:,.0f}",
                "Output Tokens": "{:,.0f}",
                "Avg Duration (ms)": "{:,.0f}",
            }),
            use_container_width=True,
        )

    with tab2:
        df = get_cost_by_practice()
        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df, x="practice", y="total_cost",
                color="practice", text_auto="$.0f",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            apply_layout(fig, title="Total Cost by Practice", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                df, x="practice", y="cost_per_user",
                color="practice", text_auto="$.0f",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            apply_layout(fig, title="Cost per User by Practice", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True)

    with tab3:
        df = get_cost_by_level()
        fig = px.bar(
            df, x="level", y="cost_per_user",
            color="total_cost", text_auto="$.0f",
            color_continuous_scale="Blues",
        )
        apply_layout(fig, title="Cost per User by Seniority Level", height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True)

    with tab4:
        df = get_top_users_by_cost(20)
        fig = px.bar(
            df, x="full_name", y="total_cost",
            color="practice", text_auto="$.0f",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        apply_layout(fig, title="Top 20 Users by Total Cost", height=450)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df[["full_name", "practice", "level", "location", "num_sessions", "request_count", "total_cost"]],
            use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Page: Usage Trends

elif page == "📈 Usage Trends":
    st.title("📈 Usage Trends")
    st.markdown("How Claude Code usage evolves over time")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Daily Trends", "Time Patterns", "Weekly Rollup"])

    with tab1:
        daily = get_daily_usage()
        daily["date"] = pd.to_datetime(daily["date"])

        metric = st.selectbox(
            "Metric",
            ["total_cost", "api_requests", "sessions", "active_users", "output_tokens"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["date"], y=daily[metric],
            mode="lines+markers", name=metric.replace("_", " ").title(),
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=4),
        ))
        # 7-day rolling average
        rolling = daily[metric].rolling(window=7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=daily["date"], y=rolling,
            mode="lines", name="7-day Average",
            line=dict(color=COLORS["warning"], width=2, dash="dash"),
        ))
        apply_layout(fig, title=f"Daily {metric.replace('_', ' ').title()}", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            hourly = get_hourly_distribution()
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=hourly["hour"], y=hourly["request_count"],
                marker_color=[
                    COLORS["primary"] if 9 <= h <= 17 else "#2a2f3e"
                    for h in hourly["hour"]
                ],
                text=hourly["request_count"],
                textposition="outside",
            ))
            apply_layout(
                fig, title="Requests by Hour of Day",
                xaxis_title="Hour (UTC)", height=400,
            )
            fig.update_xaxes(dtick=1)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Business hours (9-17) highlighted in blue")

        with col2:
            dow = get_day_of_week_distribution()
            day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            dow["day_name"] = dow["day_of_week"].map(lambda x: day_names[x])

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=dow["day_name"], y=dow["request_count"],
                marker_color=[
                    COLORS["danger"] if d in [0, 6] else COLORS["success"]
                    for d in dow["day_of_week"]
                ],
                text=dow["request_count"],
                textposition="outside",
            ))
            apply_layout(fig, title="Requests by Day of Week", height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Weekdays in green, weekends in red")

    with tab3:
        weekly = get_weekly_usage()
        weekly["week_start"] = pd.to_datetime(weekly["week_start"])

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=weekly["week_start"], y=weekly["total_cost"],
            name="Weekly Cost", marker_color=COLORS["primary"],
            opacity=0.8,
        ))
        fig.add_trace(go.Scatter(
            x=weekly["week_start"], y=weekly["active_users"],
            name="Active Users", yaxis="y2",
            line=dict(color=COLORS["success"], width=3),
            mode="lines+markers",
        ))
        apply_layout(
            fig, title="Weekly Cost & Active Users", height=400,
            yaxis_title="Cost ($)",
            yaxis2=dict(
                title="Active Users", overlaying="y", side="right",
                gridcolor="rgba(0,0,0,0)", color="#8b95a5",
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(weekly, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: Model Analysis

elif page == "🤖 Model Analysis":
    st.title("🤖 Model Analysis")
    st.markdown("Comparing Claude model performance, cost, and adoption")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Model Comparison", "Adoption Over Time"])

    with tab1:
        efficiency = get_model_efficiency()

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                efficiency, x="model", y="cost_per_1k_output",
                color="model", color_discrete_map=MODEL_COLORS,
                text_auto="$.4f",
            )
            apply_layout(fig, title="Cost per 1K Output Tokens", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                efficiency, x="model", y="tokens_per_second",
                color="model", color_discrete_map=MODEL_COLORS,
                text_auto=".1f",
            )
            apply_layout(fig, title="Output Tokens per Second (Speed)", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Scatter: cost vs speed
        fig = px.scatter(
            efficiency, x="avg_duration_ms", y="avg_cost",
            size="requests", color="model",
            color_discrete_map=MODEL_COLORS,
            hover_data=["requests", "tokens_per_second"],
            size_max=50,
        )
        apply_layout(
            fig, title="Model Tradeoff: Cost vs Speed (bubble size = request count)",
            xaxis_title="Avg Duration (ms)", yaxis_title="Avg Cost ($)",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            efficiency.rename(columns={
                "model": "Model", "requests": "Requests",
                "avg_duration_ms": "Avg Duration (ms)",
                "avg_output_tokens": "Avg Output Tokens",
                "avg_cost": "Avg Cost ($)",
                "cost_per_1k_output": "Cost/1K Output",
                "tokens_per_second": "Tokens/sec",
            }).style.format({
                "Avg Duration (ms)": "{:,.0f}",
                "Avg Output Tokens": "{:,.0f}",
                "Avg Cost ($)": "${:,.4f}",
                "Cost/1K Output": "${:,.4f}",
                "Tokens/sec": "{:,.1f}",
            }),
            use_container_width=True,
        )

    with tab2:
        model_time = get_model_usage_over_time()
        model_time["date"] = pd.to_datetime(model_time["date"])

        fig = px.area(
            model_time, x="date", y="request_count",
            color="model", color_discrete_map=MODEL_COLORS,
            groupnorm="percent",
        )
        apply_layout(
            fig, title="Model Adoption Over Time (% of Daily Requests)",
            yaxis_title="% of Requests", height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Absolute counts
        fig = px.line(
            model_time, x="date", y="request_count",
            color="model", color_discrete_map=MODEL_COLORS,
        )
        apply_layout(fig, title="Daily Request Count by Model", height=400)
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: Tool Analysis

elif page == "🔧 Tool Analysis":
    st.title("🔧 Tool Analysis")
    st.markdown("How developers interact with Claude Code's tools")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Usage & Acceptance", "Success Rates", "By Practice"])

    with tab1:
        tool_usage = get_tool_usage_summary()

        fig = px.bar(
            tool_usage, x="tool_name", y="total_decisions",
            color="accept_rate", text_auto=True,
            color_continuous_scale="RdYlGn",
            range_color=[80, 100],
        )
        apply_layout(
            fig, title="Tool Usage Frequency (color = acceptance rate %)",
            height=450,
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(tool_usage, use_container_width=True)

    with tab2:
        tool_success = get_tool_success_rates()

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                tool_success, x="tool_name", y="success_rate",
                color="success_rate",
                color_continuous_scale="RdYlGn",
                range_color=[85, 100],
                text_auto=".1f",
            )
            apply_layout(fig, title="Tool Success Rates (%)", height=400)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                tool_success, x="tool_name", y="avg_duration_ms",
                color="tool_name", text_auto=".0f",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            apply_layout(fig, title="Avg Execution Duration (ms)", showlegend=False, height=400)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(tool_success, use_container_width=True)

    with tab3:
        tool_practice = get_tool_usage_by_practice()

        # Pivot to heatmap
        pivot = tool_practice.pivot_table(
            values="usage_count", index="practice", columns="tool_name",
            fill_value=0, aggfunc="sum",
        )

        fig = px.imshow(
            pivot, text_auto=True,
            color_continuous_scale="Blues",
            aspect="auto",
        )
        apply_layout(fig, title="Tool Usage Heatmap by Practice", height=400)
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: Error Analysis

elif page == "❌ Error Analysis":
    st.title("❌ Error Analysis")
    st.markdown("Understanding API failures and their patterns")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        error_summary = get_error_summary()
        # Shorten error messages for display
        error_summary["error_short"] = error_summary["error"].str[:50] + "..."
        fig = px.bar(
            error_summary, x="error_count", y="error_short",
            orientation="h", color="status_code",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        apply_layout(fig, title="Errors by Type & Status Code", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        errors_model = get_errors_by_model()
        fig = px.bar(
            errors_model, x="model", y="error_count",
            color="status_code",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        apply_layout(fig, title="Errors by Model", height=400)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Error trend
    error_trend = get_error_trend()
    error_trend["date"] = pd.to_datetime(error_trend["date"])
    error_agg = error_trend.groupby("date")["error_count"].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=error_agg["date"], y=error_agg["error_count"],
        fill="tozeroy", name="Daily Errors",
        line=dict(color=COLORS["danger"], width=2),
        fillcolor="rgba(239, 68, 68, 0.15)",
    ))
    apply_layout(fig, title="Daily Error Count Over Time", height=350)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Error Details")
    st.dataframe(error_summary[["error", "status_code", "error_count", "avg_retry_attempt"]], use_container_width=True)


# ---------------------------------------------------------------------------
# Page: User Insights
# ---------------------------------------------------------------------------

elif page == "👥 User Insights":
    st.title("👥 User Insights")
    st.markdown("Deep dive into individual user and team behavior")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["User Engagement", "Environment", "Prompts"])

    with tab1:
        engagement = get_user_engagement()

        col1, col2 = st.columns(2)

        with col1:
            fig = px.scatter(
                engagement, x="sessions", y="total_cost",
                color="practice", size="total_requests",
                hover_data=["full_name", "level", "active_days"],
                size_max=30,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            apply_layout(
                fig, title="User Engagement: Sessions vs Cost",
                xaxis_title="Sessions", yaxis_title="Total Cost ($)",
                height=450,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                engagement, x="active_days", y="total_cost",
                color="level", size="total_requests",
                hover_data=["full_name", "practice"],
                size_max=30,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            apply_layout(
                fig, title="Active Days vs Cost (color = level)",
                xaxis_title="Active Days", yaxis_title="Total Cost ($)",
                height=450,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Full User Table")
        st.dataframe(
            engagement[["full_name", "practice", "level", "location", "sessions",
                         "total_requests", "total_cost", "active_days"]]
            .style.format({"total_cost": "${:,.2f}"}),
            use_container_width=True,
            height=400,
        )

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            terminal = get_usage_by_terminal()
            fig = px.pie(
                terminal, values="sessions", names="terminal_type",
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            apply_layout(fig, title="Sessions by Terminal/IDE", height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            os_df = get_usage_by_os()
            os_df["label"] = os_df["os_type"] + " (" + os_df["host_arch"] + ")"
            fig = px.pie(
                os_df, values="sessions", names="label",
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            apply_layout(fig, title="Sessions by OS", height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Location
        location = get_cost_by_location()
        fig = px.bar(
            location, x="location", y="total_cost",
            color="location", text_auto="$.0f",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        apply_layout(fig, title="Total Cost by Location", showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        prompt_stats = get_prompt_length_stats()

        # Average prompt length by level
        level_prompts = prompt_stats.groupby("level").agg({
            "prompt_count": "sum",
            "avg_length": "mean",
        }).reset_index()

        fig = px.bar(
            level_prompts, x="level", y="avg_length",
            color="avg_length", text_auto=".0f",
            color_continuous_scale="Viridis",
        )
        apply_layout(fig, title="Average Prompt Length by Seniority Level", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # By practice
        practice_prompts = prompt_stats.groupby("practice").agg({
            "prompt_count": "sum",
            "avg_length": "mean",
        }).reset_index()

        fig = px.bar(
            practice_prompts, x="practice", y="avg_length",
            color="practice", text_auto=".0f",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        apply_layout(fig, title="Average Prompt Length by Practice", showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: Anomaly Detection 

elif page == "🔍 Anomaly Detection":
    st.title("🔍 Anomaly Detection")
    st.markdown("Flagging unusual spending patterns using statistical methods")
    st.markdown("---")

    st.subheader("Daily Cost Anomalies")
    st.markdown(
        "Days where total cost exceeds 2 standard deviations from the 7-day rolling average "
        "are flagged as potential anomalies."
    )

    anomaly_df = get_daily_cost_with_stats()

    fig = go.Figure()

    # Confidence band
    fig.add_trace(go.Scatter(
        x=anomaly_df["date"], y=anomaly_df["upper_bound"],
        mode="lines", line=dict(width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=anomaly_df["date"], y=anomaly_df["lower_bound"],
        mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(37, 99, 235, 0.1)",
        name="Normal Range (2σ)",
    ))

    # Actual cost
    fig.add_trace(go.Scatter(
        x=anomaly_df["date"], y=anomaly_df["total_cost"],
        mode="lines+markers", name="Daily Cost",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=4),
    ))

    # Rolling average
    fig.add_trace(go.Scatter(
        x=anomaly_df["date"], y=anomaly_df["cost_7d_avg"],
        mode="lines", name="7-day Average",
        line=dict(color=COLORS["warning"], width=2, dash="dash"),
    ))

    # Anomaly points
    anomalies = anomaly_df[anomaly_df["is_anomaly"]]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies["date"], y=anomalies["total_cost"],
            mode="markers", name="Anomaly",
            marker=dict(color=COLORS["danger"], size=12, symbol="x"),
        ))

    apply_layout(fig, title="Daily Cost with Anomaly Detection", height=500)
    st.plotly_chart(fig, use_container_width=True)

    num_anomalies = anomaly_df["is_anomaly"].sum()
    st.metric("Days Flagged as Anomalies", f"{num_anomalies} / {len(anomaly_df)}")

    st.markdown("---")

    st.subheader("User-Level Spending Anomalies")
    st.markdown(
        "Users whose daily spending exceeds 2 standard deviations above their personal average. "
        "These could indicate unusually complex tasks, runaway loops, or misconfigured sessions."
    )

    user_anomalies = get_user_cost_anomalies()

    if not user_anomalies.empty:
        fig = px.scatter(
            user_anomalies, x="date", y="daily_cost",
            color="practice", size="daily_cost",
            hover_data=["full_name", "avg_daily_cost", "threshold"],
            size_max=25,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        apply_layout(
            fig, title="User Spending Anomalies",
            xaxis_title="Date", yaxis_title="Daily Cost ($)",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            user_anomalies[["full_name", "practice", "date", "daily_cost", "avg_daily_cost", "threshold"]]
            .rename(columns={
                "full_name": "Name", "practice": "Practice", "date": "Date",
                "daily_cost": "Daily Cost ($)", "avg_daily_cost": "Avg Daily ($)",
                "threshold": "Threshold ($)",
            })
            .style.format({
                "Daily Cost ($)": "${:,.2f}",
                "Avg Daily ($)": "${:,.2f}",
                "Threshold ($)": "${:,.2f}",
            }),
            use_container_width=True,
        )
    else:
        st.info("No user-level anomalies detected.")
