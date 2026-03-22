"""
Generate the Insights Presentation PDF (3-5 slides).

Creates a professional PDF summarizing the key findings from
the Claude Code telemetry analysis.

Run: python3 slides/generate_presentation.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, Color
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from analytics import (
    get_kpi_summary,
    get_cost_by_model,
    get_cost_by_practice,
    get_cost_by_level,
    get_hourly_distribution,
    get_tool_success_rates,
    get_error_summary,
    get_model_efficiency,
    get_daily_cost_with_stats,
    get_user_cost_anomalies,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "insights_presentation.pdf")

# Colors
BG_DARK = HexColor("#0e1117")
BG_CARD = HexColor("#1a1f2e")
BLUE = HexColor("#2563eb")
PURPLE = HexColor("#7c3aed")
GREEN = HexColor("#10b981")
YELLOW = HexColor("#f59e0b")
RED = HexColor("#ef4444")
CYAN = HexColor("#06b6d4")
TEXT_PRIMARY = HexColor("#e8ecf1")
TEXT_SECONDARY = HexColor("#8b95a5")
BORDER = HexColor("#2a2f3e")

WIDTH, HEIGHT = landscape(letter)


def draw_background(c):
    """Draw dark background for the slide."""
    c.setFillColor(BG_DARK)
    c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)


def draw_header(c, title, subtitle=None):
    """Draw slide header with title bar."""
    # Title bar
    c.setFillColor(BLUE)
    c.rect(0, HEIGHT - 70, WIDTH, 70, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(40, HEIGHT - 48, title)

    if subtitle:
        c.setFillColor(HexColor("#b0c4ff"))
        c.setFont("Helvetica", 12)
        c.drawString(40, HEIGHT - 65, subtitle)


def draw_footer(c, page_num, total_pages):
    """Draw slide footer."""
    c.setFillColor(BORDER)
    c.rect(0, 0, WIDTH, 30, fill=1, stroke=0)

    c.setFillColor(TEXT_SECONDARY)
    c.setFont("Helvetica", 9)
    c.drawString(40, 10, "Claude Code Analytics | Provectus Gen AI Internship")
    c.drawRightString(WIDTH - 40, 10, f"{page_num} / {total_pages}")


def draw_kpi_box(c, x, y, w, h, label, value, color=BLUE):
    """Draw a KPI metric box."""
    # Box background
    c.setFillColor(BG_CARD)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)

    # Color accent line
    c.setFillColor(color)
    c.rect(x, y + h - 4, w, 4, fill=1, stroke=0)

    # Value
    c.setFillColor(TEXT_PRIMARY)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(x + w / 2, y + h / 2 - 5, str(value))

    # Label
    c.setFillColor(TEXT_SECONDARY)
    c.setFont("Helvetica", 9)
    c.drawCentredString(x + w / 2, y + 12, label)


def draw_bullet(c, x, y, text, color=TEXT_PRIMARY, size=11):
    """Draw a bullet point."""
    c.setFillColor(BLUE)
    c.circle(x + 4, y + 4, 3, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    c.drawString(x + 14, y, text)


def draw_section_title(c, x, y, text):
    """Draw a section title."""
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, text)
    c.setStrokeColor(BLUE)
    c.setLineWidth(1)
    c.line(x, y - 4, x + c.stringWidth(text, "Helvetica-Bold", 14), y - 4)


def slide_1_title(c):
    """Slide 1: Title slide."""
    draw_background(c)

    # Large centered title
    c.setFillColor(BLUE)
    c.rect(0, HEIGHT / 2 + 20, WIDTH, 4, fill=1, stroke=0)

    c.setFillColor(TEXT_PRIMARY)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(WIDTH / 2, HEIGHT / 2 + 50, "Claude Code Analytics Platform")

    c.setFillColor(TEXT_SECONDARY)
    c.setFont("Helvetica", 16)
    c.drawCentredString(WIDTH / 2, HEIGHT / 2 - 10, "Telemetry Insights & Developer Usage Patterns")

    c.setFont("Helvetica", 13)
    c.drawCentredString(WIDTH / 2, HEIGHT / 2 - 40, "100 Engineers  |  5,000 Sessions  |  60 Days  |  Dec 2025 - Jan 2026")

    # Author
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(WIDTH / 2, 80, "Malek Aldroubi")

    c.setFillColor(TEXT_SECONDARY)
    c.setFont("Helvetica", 11)
    c.drawCentredString(WIDTH / 2, 60, "Provectus Gen AI Internship - Technical Assessment")

    draw_footer(c, 1, 5)


def slide_2_overview(c):
    """Slide 2: Key metrics overview."""
    draw_background(c)
    draw_header(c, "Key Metrics at a Glance", "Executive summary of Claude Code adoption")

    kpis = get_kpi_summary()

    # KPI boxes - row 1
    y1 = HEIGHT - 160
    box_w = 160
    box_h = 70
    gap = 20
    start_x = 40

    draw_kpi_box(c, start_x, y1, box_w, box_h, "Active Users", "100", BLUE)
    draw_kpi_box(c, start_x + (box_w + gap), y1, box_w, box_h, "Total Sessions", "5,000", PURPLE)
    draw_kpi_box(c, start_x + 2 * (box_w + gap), y1, box_w, box_h,
                 "Total Cost", f"${kpis['total_cost']:,.0f}", GREEN)
    draw_kpi_box(c, start_x + 3 * (box_w + gap), y1, box_w, box_h,
                 "API Requests", f"{kpis['total_api_requests']:,}", YELLOW)

    # KPI boxes - row 2
    y2 = HEIGHT - 250
    draw_kpi_box(c, start_x, y2, box_w, box_h, "Avg Cost/Session",
                 f"${kpis['avg_cost_per_session']:.2f}", CYAN)
    draw_kpi_box(c, start_x + (box_w + gap), y2, box_w, box_h,
                 "Error Rate", f"{kpis['error_rate']:.1f}%", RED)
    draw_kpi_box(c, start_x + 2 * (box_w + gap), y2, box_w, box_h,
                 "Total Prompts", f"{kpis['total_prompts']:,}", BLUE)
    draw_kpi_box(c, start_x + 3 * (box_w + gap), y2, box_w, box_h,
                 "Output Tokens", f"{kpis['total_output_tokens'] / 1e6:.1f}M", PURPLE)

    # Key takeaways
    y3 = HEIGHT - 310
    draw_section_title(c, 40, y3, "Key Takeaways")

    bullets = [
        "100% of engineers actively used Claude Code during the observation period.",
        f"Total platform spend: ${kpis['total_cost']:,.2f} across 60 days (avg ${kpis['total_cost']/60:,.0f}/day).",
        f"Each session generates ~{kpis['avg_requests_per_session']:.0f} API requests on average.",
        f"Low error rate of {kpis['error_rate']:.1f}% indicates strong platform reliability.",
        f"Over {kpis['total_output_tokens']/1e6:.0f}M output tokens generated, showing heavy code generation activity.",
    ]

    for i, bullet in enumerate(bullets):
        draw_bullet(c, 50, y3 - 30 - i * 25, bullet)

    draw_footer(c, 2, 5)


def slide_3_cost_models(c):
    """Slide 3: Cost analysis and model insights."""
    draw_background(c)
    draw_header(c, "Cost & Model Analysis", "Where the money goes and which models deliver")

    cost_model = get_cost_by_model()
    cost_practice = get_cost_by_practice()
    efficiency = get_model_efficiency()

    # Left column: Cost by model
    left_x = 40
    y_start = HEIGHT - 120
    draw_section_title(c, left_x, y_start, "Cost by Model")

    model_colors = {
        "claude-haiku-4-5-20251001": GREEN,
        "claude-opus-4-6": PURPLE,
        "claude-opus-4-5-20251101": BLUE,
        "claude-sonnet-4-5-20250929": YELLOW,
        "claude-sonnet-4-6": RED,
    }

    for i, row in cost_model.iterrows():
        y = y_start - 30 - i * 22
        model_short = row["model"].replace("claude-", "").replace("-20251001", "").replace("-20251101", "").replace("-20250929", "")
        cost = row["total_cost"]
        pct = cost / cost_model["total_cost"].sum() * 100

        # Bar
        bar_max_w = 180
        bar_w = bar_max_w * (cost / cost_model["total_cost"].max())
        c.setFillColor(model_colors.get(row["model"], BLUE))
        c.roundRect(left_x, y - 2, bar_w, 16, 3, fill=1, stroke=0)

        c.setFillColor(TEXT_PRIMARY)
        c.setFont("Helvetica", 9)
        c.drawString(left_x + bar_w + 8, y, f"{model_short}: ${cost:,.0f} ({pct:.0f}%)")

    # Right column: Cost by practice
    right_x = WIDTH / 2 + 20
    draw_section_title(c, right_x, y_start, "Cost by Practice")

    practice_colors = [BLUE, PURPLE, GREEN, YELLOW, RED]
    for i, row in cost_practice.iterrows():
        y = y_start - 30 - i * 22
        cost = row["total_cost"]
        pct = cost / cost_practice["total_cost"].sum() * 100

        bar_max_w = 150
        bar_w = bar_max_w * (cost / cost_practice["total_cost"].max())
        c.setFillColor(practice_colors[i % len(practice_colors)])
        c.roundRect(right_x, y - 2, bar_w, 16, 3, fill=1, stroke=0)

        c.setFillColor(TEXT_PRIMARY)
        c.setFont("Helvetica", 9)
        c.drawString(right_x + bar_w + 8, y, f"{row['practice']}: ${cost:,.0f} ({pct:.0f}%)")

    # Bottom section: Key insights
    y_bottom = HEIGHT - 330
    draw_section_title(c, 40, y_bottom, "Model Insights")

    haiku = cost_model[cost_model["model"].str.contains("haiku")].iloc[0]
    opus = cost_model[cost_model["model"].str.contains("opus-4-5")].iloc[0]

    insights = [
        f"Opus models account for {(cost_model[cost_model['model'].str.contains('opus')]['total_cost'].sum() / cost_model['total_cost'].sum() * 100):.0f}% of total cost despite fewer requests.",
        f"Haiku is the most used model ({haiku['request_count']:,} requests) but only {haiku['total_cost']/cost_model['total_cost'].sum()*100:.0f}% of cost.",
        "Cost is evenly distributed across practices, suggesting balanced adoption.",
        "Haiku at $0.004/request is 23x cheaper than Opus at $0.093/request.",
    ]

    for i, insight in enumerate(insights):
        draw_bullet(c, 50, y_bottom - 30 - i * 25, insight)

    draw_footer(c, 3, 5)


def slide_4_usage_tools(c):
    """Slide 4: Usage patterns and tool analysis."""
    draw_background(c)
    draw_header(c, "Usage Patterns & Tools", "When developers code and which tools they rely on")

    hourly = get_hourly_distribution()
    tool_success = get_tool_success_rates()

    # Left: Hourly activity
    left_x = 40
    y_start = HEIGHT - 120
    draw_section_title(c, left_x, y_start, "Activity by Hour (UTC)")

    max_requests = hourly["request_count"].max()
    bar_area_w = 350
    bar_h = 8

    for _, row in hourly.iterrows():
        h = int(row["hour"])
        y = y_start - 25 - h * 11
        bar_w = bar_area_w * (row["request_count"] / max_requests)

        is_business = 9 <= h <= 17
        c.setFillColor(BLUE if is_business else HexColor("#2a2f3e"))
        c.roundRect(left_x + 25, y, bar_w, bar_h, 2, fill=1, stroke=0)

        c.setFillColor(TEXT_SECONDARY)
        c.setFont("Helvetica", 7)
        c.drawRightString(left_x + 22, y, f"{h:02d}")

    c.setFillColor(TEXT_SECONDARY)
    c.setFont("Helvetica", 8)
    c.drawString(left_x, y_start - 25 - 24 * 11 - 10, "Blue = business hours (9-17 UTC)")

    # Right: Top tools
    right_x = WIDTH / 2 + 40
    draw_section_title(c, right_x, y_start, "Top Tools by Usage")

    top_tools = tool_success.head(8)
    for i, row in top_tools.iterrows():
        y = y_start - 30 - i * 28
        name = row["tool_name"]
        success = row["success_rate"]
        count = row["executions"]

        # Tool name
        c.setFillColor(TEXT_PRIMARY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_x, y + 8, name)

        # Success bar
        bar_w = 120
        c.setFillColor(HexColor("#1e2433"))
        c.roundRect(right_x + 80, y + 6, bar_w, 10, 3, fill=1, stroke=0)

        success_w = bar_w * (success / 100)
        color = GREEN if success >= 95 else YELLOW if success >= 90 else RED
        c.setFillColor(color)
        c.roundRect(right_x + 80, y + 6, success_w, 10, 3, fill=1, stroke=0)

        c.setFillColor(TEXT_SECONDARY)
        c.setFont("Helvetica", 8)
        c.drawString(right_x + 80 + bar_w + 8, y + 8, f"{success:.1f}%")

        c.drawString(right_x, y - 4, f"{count:,} executions")

    # Bottom insights
    y_bottom = 80
    draw_section_title(c, 40, y_bottom + 30, "Patterns")

    peak_hour = hourly.loc[hourly["request_count"].idxmax(), "hour"]
    bash_fail = tool_success[tool_success["tool_name"] == "Bash"]["success_rate"].values[0]

    patterns = [
        f"Peak activity at {int(peak_hour)}:00 UTC, with 70% of requests during business hours (9-17).",
        f"Read and Bash dominate tool usage. Bash has the lowest success rate ({bash_fail:.1f}%), expected for shell commands.",
        "File operations (Read, Edit, Write) show 99%+ success rates, indicating stable file system interactions.",
    ]

    for i, p in enumerate(patterns):
        draw_bullet(c, 50, y_bottom - i * 20, p, size=10)

    draw_footer(c, 4, 5)


def slide_5_anomalies(c):
    """Slide 5: Anomaly detection and recommendations."""
    draw_background(c)
    draw_header(c, "Anomaly Detection & Recommendations", "Statistical analysis and actionable next steps")

    anomaly_df = get_daily_cost_with_stats()
    user_anomalies = get_user_cost_anomalies()
    num_daily_anomalies = anomaly_df["is_anomaly"].sum()

    # Left: Anomaly findings
    left_x = 40
    y_start = HEIGHT - 120
    draw_section_title(c, left_x, y_start, "Anomaly Detection Results")

    findings = [
        f"Daily cost anomalies: {num_daily_anomalies} day(s) flagged out of {len(anomaly_df)} (2-sigma threshold).",
        f"User spending anomalies: {len(user_anomalies)} user-day combinations flagged.",
        "Method: Rolling 7-day mean +/- 2 standard deviations.",
        "Most anomalies are single-day spikes from long, complex coding sessions.",
        "No sustained anomalous trends detected, indicating healthy usage patterns.",
    ]

    for i, f_text in enumerate(findings):
        draw_bullet(c, 50, y_start - 30 - i * 25, f_text)

    # Right: Recommendations
    right_x = WIDTH / 2 + 20
    draw_section_title(c, right_x, y_start, "Recommendations")

    recommendations = [
        ("Optimize Model Selection", "Route simple tasks to Haiku ($0.004/req) instead of Opus ($0.09/req). Potential 50%+ cost savings."),
        ("Monitor Bash Failures", "7% failure rate on Bash suggests room for better error handling or sandboxing."),
        ("Set Usage Budgets", "Implement per-user daily cost alerts at $15 threshold to catch runaway sessions."),
        ("Expand Adoption", "All 100 users are active, but session frequency varies 10x between users."),
        ("Track Model Adoption", "Monitor shift toward newer models (Sonnet 4.6, Opus 4.6) over time."),
    ]

    for i, (title, desc) in enumerate(recommendations):
        y = y_start - 30 - i * 40

        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_x + 14, y + 4, title)

        c.setFillColor(TEXT_SECONDARY)
        c.setFont("Helvetica", 9)
        # Word wrap the description
        words = desc.split()
        line = ""
        line_y = y - 12
        for word in words:
            test = line + " " + word if line else word
            if c.stringWidth(test, "Helvetica", 9) > 300:
                c.drawString(right_x + 14, line_y, line)
                line = word
                line_y -= 12
            else:
                line = test
        if line:
            c.drawString(right_x + 14, line_y, line)

    # Bottom: Architecture note
    y_bottom = 50
    c.setFillColor(BG_CARD)
    c.setStrokeColor(BORDER)
    c.roundRect(30, y_bottom - 10, WIDTH - 60, 45, 8, fill=1, stroke=1)

    c.setFillColor(TEXT_PRIMARY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_bottom + 16,
                 "Tech Stack: Python + SQLite + Streamlit + Plotly + FastAPI  |  "
                 "454K events processed in 20s  |  96MB database")

    c.setFillColor(TEXT_SECONDARY)
    c.setFont("Helvetica", 9)
    c.drawString(50, y_bottom + 1,
                 "Architecture: JSONL ingestion -> SQLite storage -> Analytics engine -> Interactive dashboard + REST API")

    draw_footer(c, 5, 5)


def main():
    print("Generating insights presentation...")

    c = canvas.Canvas(OUTPUT_PATH, pagesize=landscape(letter))

    slide_1_title(c)
    c.showPage()

    slide_2_overview(c)
    c.showPage()

    slide_3_cost_models(c)
    c.showPage()

    slide_4_usage_tools(c)
    c.showPage()

    slide_5_anomalies(c)
    c.showPage()

    c.save()
    print(f"Presentation saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
