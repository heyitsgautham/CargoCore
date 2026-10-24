"""
test_sql_validator.py
Unit tests for the SQL validation layer.
"""
import pytest

from app.services.sql_validator import SQLValidationError, validate_sql

# ── Valid SELECT queries ──────────────────────────────────────────────────────


class TestValidQueries:
    def test_simple_select(self):
        sql = validate_sql("SELECT name, email FROM users")
        assert "SELECT" in sql
        assert "LIMIT 50" in sql

    def test_select_with_join(self):
        sql = validate_sql(
            "SELECT u.name, r.name FROM users u JOIN roles r ON u.role_id = r.id"
        )
        assert "JOIN" in sql
        assert "LIMIT 50" in sql

    def test_select_count(self):
        sql = validate_sql("SELECT COUNT(*) FROM users")
        assert "COUNT(*)" in sql

    def test_select_with_where(self):
        sql = validate_sql("SELECT name FROM users WHERE is_active = true")
        assert "WHERE" in sql

    def test_select_with_group_by(self):
        sql = validate_sql(
            "SELECT r.name, COUNT(u.id) FROM roles r "
            "LEFT JOIN users u ON r.id = u.role_id GROUP BY r.name"
        )
        assert "GROUP BY" in sql

    def test_select_with_existing_limit(self):
        sql = validate_sql("SELECT name FROM users LIMIT 10")
        assert "LIMIT 10" in sql

    def test_select_with_order_by(self):
        sql = validate_sql("SELECT name, created_at FROM users ORDER BY created_at DESC")
        assert "ORDER BY" in sql

    def test_simple_expression(self):
        """SELECT 1 or SELECT NOW() should pass."""
        sql = validate_sql("SELECT 1")
        assert "SELECT 1" in sql

    def test_roles_only_query(self):
        sql = validate_sql("SELECT name FROM roles")
        assert "roles" in sql

    def test_left_join(self):
        sql = validate_sql(
            "SELECT r.name, COUNT(u.id) as cnt FROM roles r "
            "LEFT JOIN users u ON r.id = u.role_id GROUP BY r.name"
        )
        assert "LEFT JOIN" in sql


# ── Blocked statement types ───────────────────────────────────────────────────


class TestBlockedStatements:
    def test_insert_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("INSERT INTO users (name) VALUES ('hacker')")

    def test_update_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("UPDATE users SET is_active = false")

    def test_delete_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("DELETE FROM users WHERE id = 1")

    def test_drop_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("DROP TABLE users")

    def test_alter_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("ALTER TABLE users ADD COLUMN hacked BOOLEAN")

    def test_truncate_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("TRUNCATE TABLE users")

    def test_create_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("CREATE TABLE hacked (id INT)")

    def test_grant_blocked(self):
        with pytest.raises(SQLValidationError, match="SELECT"):
            validate_sql("GRANT ALL ON users TO hacker")


# ── Dangerous patterns ────────────────────────────────────────────────────────


class TestDangerousPatterns:
    def test_select_into_blocked(self):
        with pytest.raises(SQLValidationError, match="INTO"):
            validate_sql("SELECT * INTO new_table FROM users")

    def test_pg_catalog_blocked(self):
        with pytest.raises(SQLValidationError, match="pg_"):
            validate_sql("SELECT * FROM pg_catalog.pg_tables")

    def test_pg_sleep_blocked(self):
        with pytest.raises(SQLValidationError, match="pg_sleep"):
            validate_sql("SELECT pg_sleep(10)")

    def test_information_schema_blocked(self):
        with pytest.raises(SQLValidationError, match="information_schema"):
            validate_sql("SELECT * FROM information_schema.tables")

    def test_do_block_blocked(self):
        with pytest.raises(SQLValidationError, match="DO"):
            validate_sql("DO $$ BEGIN PERFORM pg_sleep(10); END $$")

    def test_multiple_statements_blocked(self):
        with pytest.raises(SQLValidationError, match="Multiple statements"):
            validate_sql("SELECT 1; DROP TABLE users")

    def test_copy_blocked(self):
        with pytest.raises(SQLValidationError, match="COPY"):
            validate_sql("COPY users TO '/tmp/dump.csv'")

    def test_dblink_blocked(self):
        with pytest.raises(SQLValidationError, match="dblink"):
            validate_sql("SELECT * FROM dblink('host=evil', 'SELECT 1') AS t(id INT)")


# ── Table whitelist ───────────────────────────────────────────────────────────


class TestTableWhitelist:
    def test_unknown_table_blocked(self):
        with pytest.raises(SQLValidationError, match="not allowed"):
            validate_sql("SELECT * FROM secret_data")

    def test_unknown_table_in_join_blocked(self):
        with pytest.raises(SQLValidationError, match="not allowed"):
            validate_sql(
                "SELECT u.name FROM users u JOIN secret_table s ON u.id = s.user_id"
            )


# ── Sensitive column blocking ─────────────────────────────────────────────────


class TestSensitiveColumns:
    def test_password_hash_blocked(self):
        with pytest.raises(SQLValidationError, match="password_hash"):
            validate_sql("SELECT name, password_hash FROM users")

    def test_password_hash_in_where_blocked(self):
        with pytest.raises(SQLValidationError, match="password_hash"):
            validate_sql("SELECT name FROM users WHERE password_hash = 'abc'")


# ── Row limit enforcement ────────────────────────────────────────────────────


class TestRowLimit:
    def test_limit_injected(self):
        sql = validate_sql("SELECT name FROM users")
        assert "LIMIT 50" in sql

    def test_excessive_limit_capped(self):
        sql = validate_sql("SELECT name FROM users LIMIT 1000")
        assert "LIMIT 50" in sql
        assert "LIMIT 1000" not in sql

    def test_reasonable_limit_preserved(self):
        sql = validate_sql("SELECT name FROM users LIMIT 10")
        assert "LIMIT 10" in sql


# ── Edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_sql_rejected(self):
        with pytest.raises(SQLValidationError, match="Empty"):
            validate_sql("")

    def test_whitespace_only_rejected(self):
        with pytest.raises(SQLValidationError, match="Empty"):
            validate_sql("   ")

    def test_semicolon_stripped(self):
        """Trailing semicolons should be stripped, not treated as multi-statement."""
        sql = validate_sql("SELECT name FROM users;")
        assert "SELECT" in sql

    def test_case_insensitive_blocking(self):
        with pytest.raises(SQLValidationError):
            validate_sql("select * from PG_CATALOG.pg_tables")
