import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "analytics.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Get a SQLite connection with optimized settings."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes."""
    conn.executescript("""
        -- Employee directory (from CSV)
        CREATE TABLE IF NOT EXISTS employees (
            email TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            practice TEXT NOT NULL,
            level TEXT NOT NULL,
            location TEXT NOT NULL
        );

        -- Sessions: one row per unique coding session
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_email TEXT NOT NULL,
            user_id TEXT,
            account_uuid TEXT,
            org_id TEXT,
            terminal_type TEXT,
            host_name TEXT,
            host_arch TEXT,
            os_type TEXT,
            os_version TEXT,
            service_version TEXT,
            started_at TEXT,
            ended_at TEXT,
            FOREIGN KEY (user_email) REFERENCES employees(email)
        );

        -- API requests: model calls with cost and token usage
        CREATE TABLE IF NOT EXISTS api_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cache_read_tokens INTEGER DEFAULT 0,
            cache_creation_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0,
            duration_ms INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        -- Tool decisions: accept/reject events for tool usage
        CREATE TABLE IF NOT EXISTS tool_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            decision TEXT NOT NULL,
            source TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        -- Tool results: execution outcomes
        CREATE TABLE IF NOT EXISTS tool_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            success INTEGER NOT NULL,
            duration_ms INTEGER DEFAULT 0,
            decision_source TEXT,
            decision_type TEXT,
            result_size_bytes INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        -- User prompts
        CREATE TABLE IF NOT EXISTS user_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            prompt_length INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        -- API errors
        CREATE TABLE IF NOT EXISTS api_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            model TEXT,
            error TEXT,
            status_code TEXT,
            attempt INTEGER DEFAULT 1,
            duration_ms INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        -- Indexes for common query patterns
        CREATE INDEX IF NOT EXISTS idx_api_requests_session ON api_requests(session_id);
        CREATE INDEX IF NOT EXISTS idx_api_requests_user ON api_requests(user_email);
        CREATE INDEX IF NOT EXISTS idx_api_requests_timestamp ON api_requests(timestamp);
        CREATE INDEX IF NOT EXISTS idx_api_requests_model ON api_requests(model);

        CREATE INDEX IF NOT EXISTS idx_tool_decisions_session ON tool_decisions(session_id);
        CREATE INDEX IF NOT EXISTS idx_tool_decisions_tool ON tool_decisions(tool_name);

        CREATE INDEX IF NOT EXISTS idx_tool_results_session ON tool_results(session_id);
        CREATE INDEX IF NOT EXISTS idx_tool_results_tool ON tool_results(tool_name);

        CREATE INDEX IF NOT EXISTS idx_user_prompts_session ON user_prompts(session_id);
        CREATE INDEX IF NOT EXISTS idx_user_prompts_user ON user_prompts(user_email);

        CREATE INDEX IF NOT EXISTS idx_api_errors_session ON api_errors(session_id);

        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_email);
    """)
    conn.commit()
