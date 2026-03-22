"""
Data ingestion pipeline 

Reads raw JSONL log batches and employee CSV, validates and transforms
the data, then loads it into the SQLite analytics Database
"""

import csv
import json
import os
import sys
import time
from typing import Generator

from database import get_connection, create_schema, DB_PATH


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
JSONL_PATH = os.path.join(DATA_DIR, "telemetry_logs.jsonl")
EMPLOYEES_PATH = os.path.join(DATA_DIR, "employees.csv")


def iter_events(jsonl_path: str) -> Generator[dict, None, None]:
    """Iterate over individual events from the JSONL logs"""
    with open(jsonl_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                batch = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  [WARN] Skipping malformed batch at line {line_num}: {e}")
                continue

            for log_event in batch.get("logEvents", []):
                try:
                    event = json.loads(log_event["message"])
                    yield event
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"  [WARN] Skipping malformed event in batch {line_num}: {e}")
                    continue


def safe_int(value, default=0):
    """convert a value to int"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    """convert a value to float"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_employees(conn) -> int:
    """Load employee CSV into the database. Returns count of rows loaded"""
    if not os.path.exists(EMPLOYEES_PATH):
        print(f"  [ERROR] Employee file not found: {EMPLOYEES_PATH}")
        return 0

    count = 0
    with open(EMPLOYEES_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                "INSERT OR REPLACE INTO employees (email, full_name, practice, level, location) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["email"], row["full_name"], row["practice"], row["level"], row["location"])
            )
            count += 1
    conn.commit()
    return count


def ingest_events(conn, jsonl_path: str) -> dict:
    """
    Parse all events and insert into the appropriate tables.
    Returns a dict with counts per event type.
    """
    counts = {
        "api_request": 0,
        "tool_decision": 0,
        "tool_result": 0,
        "user_prompt": 0,
        "api_error": 0,
        "skipped": 0,
    }
    sessions_seen = {}  # session_id -> {user_email, first_ts, last_ts, ...}

    # Batch inserts for performance
    api_requests_batch = []
    tool_decisions_batch = []
    tool_results_batch = []
    user_prompts_batch = []
    api_errors_batch = []

    BATCH_SIZE = 5000

    def flush_batches():
        if api_requests_batch:
            conn.executemany(
                "INSERT INTO api_requests "
                "(session_id, user_email, timestamp, model, input_tokens, output_tokens, "
                "cache_read_tokens, cache_creation_tokens, cost_usd, duration_ms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                api_requests_batch
            )
            api_requests_batch.clear()

        if tool_decisions_batch:
            conn.executemany(
                "INSERT INTO tool_decisions "
                "(session_id, user_email, timestamp, tool_name, decision, source) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                tool_decisions_batch
            )
            tool_decisions_batch.clear()

        if tool_results_batch:
            conn.executemany(
                "INSERT INTO tool_results "
                "(session_id, user_email, timestamp, tool_name, success, duration_ms, "
                "decision_source, decision_type, result_size_bytes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tool_results_batch
            )
            tool_results_batch.clear()

        if user_prompts_batch:
            conn.executemany(
                "INSERT INTO user_prompts "
                "(session_id, user_email, timestamp, prompt_length) "
                "VALUES (?, ?, ?, ?)",
                user_prompts_batch
            )
            user_prompts_batch.clear()

        if api_errors_batch:
            conn.executemany(
                "INSERT INTO api_errors "
                "(session_id, user_email, timestamp, model, error, status_code, attempt, duration_ms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                api_errors_batch
            )
            api_errors_batch.clear()

        conn.commit()

    total = 0
    for event in iter_events(jsonl_path):
        attrs = event.get("attributes", {})
        resource = event.get("resource", {})
        event_name = attrs.get("event.name", "")
        session_id = attrs.get("session.id", "")
        user_email = attrs.get("user.email", "")
        timestamp = attrs.get("event.timestamp", "")

        # Track session metadata
        if session_id and session_id not in sessions_seen:
            sessions_seen[session_id] = {
                "user_email": user_email,
                "user_id": attrs.get("user.id", ""),
                "account_uuid": attrs.get("user.account_uuid", ""),
                "org_id": attrs.get("organization.id", ""),
                "terminal_type": attrs.get("terminal.type", ""),
                "host_name": resource.get("host.name", ""),
                "host_arch": resource.get("host.arch", ""),
                "os_type": resource.get("os.type", ""),
                "os_version": resource.get("os.version", ""),
                "service_version": resource.get("service.version", ""),
                "started_at": timestamp,
                "ended_at": timestamp,
            }
        elif session_id in sessions_seen:
            if timestamp > sessions_seen[session_id]["ended_at"]:
                sessions_seen[session_id]["ended_at"] = timestamp

        if event_name == "api_request":
            api_requests_batch.append((
                session_id, user_email, timestamp,
                attrs.get("model", "unknown"),
                safe_int(attrs.get("input_tokens")),
                safe_int(attrs.get("output_tokens")),
                safe_int(attrs.get("cache_read_tokens")),
                safe_int(attrs.get("cache_creation_tokens")),
                safe_float(attrs.get("cost_usd")),
                safe_int(attrs.get("duration_ms")),
            ))
            counts["api_request"] += 1

        elif event_name == "tool_decision":
            tool_decisions_batch.append((
                session_id, user_email, timestamp,
                attrs.get("tool_name", "unknown"),
                attrs.get("decision", ""),
                attrs.get("source", ""),
            ))
            counts["tool_decision"] += 1

        elif event_name == "tool_result":
            success_str = attrs.get("success", "false").lower()
            tool_results_batch.append((
                session_id, user_email, timestamp,
                attrs.get("tool_name", "unknown"),
                1 if success_str == "true" else 0,
                safe_int(attrs.get("duration_ms")),
                attrs.get("decision_source", ""),
                attrs.get("decision_type", ""),
                safe_int(attrs.get("tool_result_size_bytes")) or None,
            ))
            counts["tool_result"] += 1

        elif event_name == "user_prompt":
            user_prompts_batch.append((
                session_id, user_email, timestamp,
                safe_int(attrs.get("prompt_length")),
            ))
            counts["user_prompt"] += 1

        elif event_name == "api_error":
            api_errors_batch.append((
                session_id, user_email, timestamp,
                attrs.get("model", ""),
                attrs.get("error", ""),
                attrs.get("status_code", ""),
                safe_int(attrs.get("attempt", 1)),
                safe_int(attrs.get("duration_ms")),
            ))
            counts["api_error"] += 1

        else:
            counts["skipped"] += 1

        total += 1
        if total % BATCH_SIZE == 0:
            flush_batches()

        if total % 50000 == 0:
            print(f"  Processed {total:,} events...")

    # Final flush
    flush_batches()

    # Insert sessions
    for sid, meta in sessions_seen.items():
        conn.execute(
            "INSERT OR REPLACE INTO sessions "
            "(session_id, user_email, user_id, account_uuid, org_id, terminal_type, "
            "host_name, host_arch, os_type, os_version, service_version, started_at, ended_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sid, meta["user_email"], meta["user_id"], meta["account_uuid"],
             meta["org_id"], meta["terminal_type"], meta["host_name"],
             meta["host_arch"], meta["os_type"], meta["os_version"],
             meta["service_version"], meta["started_at"], meta["ended_at"])
        )
    conn.commit()
    counts["sessions"] = len(sessions_seen)

    return counts


def validate_data(conn) -> None:
    """Run basic validation checks on the loaded data."""
    checks = [
        ("Employees", "SELECT COUNT(*) FROM employees"),
        ("Sessions", "SELECT COUNT(*) FROM sessions"),
        ("API Requests", "SELECT COUNT(*) FROM api_requests"),
        ("Tool Decisions", "SELECT COUNT(*) FROM tool_decisions"),
        ("Tool Results", "SELECT COUNT(*) FROM tool_results"),
        ("User Prompts", "SELECT COUNT(*) FROM user_prompts"),
        ("API Errors", "SELECT COUNT(*) FROM api_errors"),
    ]

    print("\n  === Data Validation ===")
    for label, query in checks:
        count = conn.execute(query).fetchone()[0]
        print(f"  {label}: {count:,} rows")

    # Check for orphaned sessions (sessions without matching employees)
    orphaned = conn.execute(
        "SELECT COUNT(DISTINCT s.user_email) FROM sessions s "
        "LEFT JOIN employees e ON s.user_email = e.email "
        "WHERE e.email IS NULL"
    ).fetchone()[0]
    print(f"  Orphaned sessions (no employee match): {orphaned}")

    # Total cost
    total_cost = conn.execute("SELECT SUM(cost_usd) FROM api_requests").fetchone()[0]
    print(f"  Total API cost: ${total_cost:,.2f}")

    # Date range
    min_ts = conn.execute("SELECT MIN(timestamp) FROM api_requests").fetchone()[0]
    max_ts = conn.execute("SELECT MAX(timestamp) FROM api_requests").fetchone()[0]
    print(f"  Date range: {min_ts[:10] if min_ts else 'N/A'} to {max_ts[:10] if max_ts else 'N/A'}")


def main():
    """Run the full ingestion pipeline."""
    print("=" * 60)
    print("Claude Code Analytics - Data Ingestion Pipeline")
    print("=" * 60)

    # Remove existing DB for clean load
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"\n  Removed existing database: {DB_PATH}")

    conn = get_connection()
    print("  Creating schema...")
    create_schema(conn)

    # Load employees
    print("\n  Loading employees...")
    emp_count = load_employees(conn)
    print(f"  Loaded {emp_count} employees")

    # Ingest telemetry events
    print(f"\n  Ingesting events from {JSONL_PATH}...")
    start_time = time.time()
    counts = ingest_events(conn, JSONL_PATH)
    elapsed = time.time() - start_time

    print(f"\n  Ingestion complete in {elapsed:.1f}s")
    for event_type, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"    {event_type}: {count:,}")

    # Validate
    validate_data(conn)

    conn.close()
    db_size = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"\n  Database size: {db_size:.1f} MB")
    print(f"  Database path: {DB_PATH}")
    print("\n  Done!")


if __name__ == "__main__":
    main()
