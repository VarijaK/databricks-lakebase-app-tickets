"""
Lakebase (Databricks-managed Postgres) connection helper.

Uses OAuth tokens via w.postgres.generate_database_credential() for secure,
time-limited authentication. Tokens are valid for 1 hour and are regenerated
on each connection.
"""

import base64
import os
from contextlib import contextmanager

import psycopg2
from databricks.sdk import WorkspaceClient
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy import event

_w = WorkspaceClient()

_SCOPE = os.environ.get("LAKEBASE_SECRET_SCOPE", "database")
_KEY = os.environ.get("LAKEBASE_SECRET_KEY", "lakebase-endpoint")
_DBNAME_KEY = os.environ.get("LAKEBASE_DBNAME_KEY", "lakebase-database")


def _get_connection_params() -> dict:
    """Fetch Lakebase endpoint and database from secrets, generate OAuth token."""
    # Get endpoint name (e.g., "projects/.../branches/.../endpoints/...")
    endpoint_secret = _w.secrets.get_secret(scope=_SCOPE, key=_KEY)
    endpoint_name = base64.b64decode(endpoint_secret.value).decode("utf-8")
    
    # Get database name (defaults to databricks_postgres)
    try:
        db_secret = _w.secrets.get_secret(scope=_SCOPE, key=_DBNAME_KEY)
        database = base64.b64decode(db_secret.value).decode("utf-8")
    except Exception:
        database = "databricks_postgres"
    
    # Get endpoint details to extract host
    endpoint = _w.postgres.get_endpoint(name=endpoint_name)
    host = endpoint.status.hosts.host
    
    # Generate OAuth token (valid for 1 hour)
    token = _w.postgres.generate_database_credential(endpoint=endpoint_name).token
    
    # Get current user
    username = _w.current_user.me().user_name
    
    return {
        "host": host,
        "dbname": database,
        "user": username,
        "password": token,
        "sslmode": "require",
        "port": 5432
    }


def _build_url_with_token() -> str:
    """Build a connection URL with a fresh OAuth token."""
    params = _get_connection_params()
    return f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['dbname']}?sslmode=require"


@contextmanager
def get_connection():
    """Yield a raw psycopg2 connection with a RealDictCursor factory."""
    params = _get_connection_params()
    conn = psycopg2.connect(**params, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def get_engine():
    """Return a SQLAlchemy engine for Lakebase with OAuth token injection."""
    # Create engine with a placeholder URL (token will be injected per connection)
    params = _get_connection_params()
    base_url = f"postgresql://{params['user']}@{params['host']}:{params['port']}/{params['dbname']}?sslmode=require"
    engine = create_engine(base_url, pool_pre_ping=True, pool_recycle=2700)
    
    # Inject fresh token on each connection
    @event.listens_for(engine, "do_connect")
    def inject_token(dialect, conn_rec, cargs, cparams):
        # Generate fresh token for each connection
        endpoint_secret = _w.secrets.get_secret(scope=_SCOPE, key=_KEY)
        endpoint_name = base64.b64decode(endpoint_secret.value).decode("utf-8")
        token = _w.postgres.generate_database_credential(endpoint=endpoint_name).token
        cparams["password"] = token
    
    return engine


def run_query(sql: str, params: tuple | dict | None = None) -> list[dict]:
    """Run a read query against Lakebase and return rows as list[dict]."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def run_write(sql: str, params: tuple | dict | None = None) -> int:
    """Run an INSERT/UPDATE/DELETE against Lakebase, return affected row count."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
