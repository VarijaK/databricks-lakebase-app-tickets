"""
One-time setup script: creates the Databricks secret scope and stores the
Lakebase connection URL for the ticket support system.
Run this locally (with the Databricks CLI configured) or from a notebook.
Never commit the resulting secret value anywhere.

Usage:
    python setup_secrets.py
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import workspace
from databricks.sdk.errors import ResourceAlreadyExists
import getpass

w = WorkspaceClient()

# Create scope if it doesn't exist
try:
    w.secrets.create_scope(scope="database")
    print("Created secret scope 'database'")
except ResourceAlreadyExists:
    print("Secret scope 'database' already exists, continuing...")
w.secrets.put_secret(
    scope="database",
    key="lakebase-url",
    string_value=getpass.getpass("Paste your Lakebase URL: ")
)

w.secrets.put_acl(
    scope="database",
    principal="users",
    permission=workspace.AclPermission.READ,
)
