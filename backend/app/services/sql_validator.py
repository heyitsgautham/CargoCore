"""
sql_validator.py
Deterministic validation layer between Gemini-generated SQL and the database.

Defense layer 2 of 4 (after system prompt, before read-only DB session
and PostgreSQL transaction-level enforcement).
"""
import re

import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis
from sqlparse.tokens import Keyword, DML

from loguru import logger

# ── Configuration ─────────────────────────────────────────────────────────────

# !! MAINTENANCE — update both files together when a new migration lands !!
# 1. Add the new table name(s) here (ALLOWED_TABLES).
# 2. Add the matching CREATE TABLE DDL in app/utils/gemini.py (DB_SCHEMA_DDL).
# Failing to update either file means the AI will refuse to query new tables
# (validator rejects them) or generate wrong SQL (Gemini has no schema for them).
# Current state: migrations 001-003 — queryable tables: users, roles.
# (ai_conversations and escalations are internal; intentionally not exposed to AI.)
ALLOWED_TABLES: set[str] = {"users", "roles"}

# Columns that must NEVER appear in query results.
BLOCKED_COLUMNS: set[str] = {"password_hash"}

# Maximum number of rows the AI can fetch.
MAX_ROW_LIMIT: int = 50

# SQL keywords / statement types that are categorically blocked.
BLOCKED_STATEMENT_TYPES: set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXECUTE",
    "COPY",
    "VACUUM",
    "CLUSTER",
    "REINDEX",
    "COMMENT",
    "LOCK",
    "SET",
    "RESET",
    "SHOW",
    "LISTEN",
    "NOTIFY",
    "PREPARE",
    "DEALLOCATE",
    "DISCARD",
    "REASSIGN",
    "DO",
    "SECURITY",
}

# Dangerous patterns that should never appear in any SQL string.
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"\bINTO\b", "INTO clause is not allowed"),
    (r"\bpg_sleep\b", "pg_sleep() is not allowed"),
    (r"\bpg_", "Access to pg_ system catalogs is not allowed"),
    (r"\binformation_schema\b", "Access to information_schema is not allowed"),
    (r"\blo_export\b", "lo_export() is not allowed"),
    (r"\blo_import\b", "lo_import() is not allowed"),
    (r"\bCOPY\b", "COPY command is not allowed"),
    (r"\bDO\s+\$", "DO $$ blocks are not allowed"),
    (r";\s*\S", "Multiple statements are not allowed"),
    (r"\bEXEC\b", "EXEC is not allowed"),
    (r"\bCALL\b", "CALL is not allowed"),
    (r"\bdblink\b", "dblink is not allowed"),
    (r"\bfile_fdw\b", "file_fdw is not allowed"),
]


class SQLValidationError(Exception):
    """Raised when SQL validation fails."""

    pass


def validate_sql(sql: str) -> str:
    """
    Validate and sanitize AI-generated SQL.

    Args:
        sql: The raw SQL string from Gemini.

    Returns:
        Sanitized SQL string safe for execution on a read-only session.

    Raises:
        SQLValidationError: If the SQL is invalid, dangerous, or violates rules.
    """
    if not sql or not sql.strip():
        raise SQLValidationError("Empty SQL query")

    sql = sql.strip().rstrip(";")

    # ── Step 1: Parse with sqlparse ───────────────────────────────────────────
    parsed_statements = sqlparse.parse(sql)

    if len(parsed_statements) != 1:
        raise SQLValidationError(
            "Multiple statements are not allowed. "
            f"Got {len(parsed_statements)} statements."
        )

    stmt = parsed_statements[0]

    # Catch blocked statement keywords early so error messages are explicit.
    sql_upper = sql.upper().strip()
    for blocked in BLOCKED_STATEMENT_TYPES:
        if sql_upper.startswith(blocked):
            raise SQLValidationError(
                f"Statement type '{blocked}' is not allowed. Only SELECT is permitted."
            )

    # ── Step 2: Verify statement type is SELECT ───────────────────────────────
    stmt_type = stmt.get_type()
    if stmt_type != "SELECT":
        raise SQLValidationError(
            f"Only SELECT statements are allowed. Got: {stmt_type or 'UNKNOWN'}"
        )

    # ── Step 3: Check for dangerous patterns ──────────────────────────────────
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            raise SQLValidationError(f"Blocked: {message}")

    # ── Step 4: Extract and validate table references ─────────────────────────
    tables = _extract_table_names(sql)
    if not tables:
        # Could be a simple SELECT 1 or SELECT NOW() — allow it
        logger.debug(f"No table references found in SQL: {sql}")
    else:
        disallowed = tables - ALLOWED_TABLES
        if disallowed:
            raise SQLValidationError(
                f"Access to table(s) {disallowed} is not allowed. "
                f"Allowed tables: {ALLOWED_TABLES}"
            )

    # ── Step 5: Block sensitive columns ───────────────────────────────────────
    sql_lower = sql.lower()
    for col in BLOCKED_COLUMNS:
        if col.lower() in sql_lower:
            raise SQLValidationError(
                f"Column '{col}' cannot be queried. It contains sensitive data."
            )

    # ── Step 6: Enforce row limit ─────────────────────────────────────────────
    sql = _enforce_limit(sql)

    logger.info(f"SQL validated successfully: {sql[:200]}")
    return sql


def _extract_table_names(sql: str) -> set[str]:
    """
    Extract table names from a SQL SELECT statement.

    Uses a regex-based approach for reliability:
    - FROM <table>
    - JOIN <table>
    """
    tables: set[str] = set()

    # Match FROM and JOIN clauses
    # Handles: FROM users, FROM users u, FROM users AS u
    # Also handles: JOIN roles, LEFT JOIN roles r, etc.
    pattern = r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    matches = re.findall(pattern, sql, re.IGNORECASE)

    for match in matches:
        table_name = match.lower().strip()
        # Filter out SQL keywords that might appear after FROM in subqueries
        if table_name not in {"select", "lateral", "unnest", "generate_series", "values"}:
            tables.add(table_name)

    return tables


def _enforce_limit(sql: str) -> str:
    """
    Inject LIMIT clause if not already present.
    """
    if re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
        # Already has a LIMIT — check if it's too high
        limit_match = re.search(r"\bLIMIT\s+(\d+)", sql, re.IGNORECASE)
        if limit_match:
            current_limit = int(limit_match.group(1))
            if current_limit > MAX_ROW_LIMIT:
                sql = re.sub(
                    r"\bLIMIT\s+\d+",
                    f"LIMIT {MAX_ROW_LIMIT}",
                    sql,
                    flags=re.IGNORECASE,
                )
        return sql

    # No LIMIT clause — add one
    # Handle potential trailing ORDER BY, then append LIMIT
    sql = f"{sql} LIMIT {MAX_ROW_LIMIT}"
    return sql
