"""
One-time setup script: creates the Databricks secret scope and stores the
Lakebase endpoint resource name for the ticket support system.
Run this locally (with the Databricks CLI configured) or from a notebook.
Never commit the resulting secret value anywhere.

Usage:
    python setup_secrets.py
    
You'll need:
1. Lakebase endpoint resource name (format: projects/<id>/branches/<id>/endpoints/<id>)
2. Database name (defaults to databricks_postgres if not provided)
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

# Store endpoint resource name
print("\nEnter your Lakebase endpoint resource name.")
print("Format: projects/<project_id>/branches/<branch_id>/endpoints/<endpoint_id>")
print("Example: projects/my-project/branches/production/endpoints/primary")
endpoint_name = getpass.getpass("Endpoint name: ")

w.secrets.put_secret(
    scope="database",
    key="lakebase-endpoint",
    string_value=endpoint_name
)
print("✓ Stored endpoint name")

# Optionally store database name
print("\nEnter your database name (press Enter to use default 'databricks_postgres'):")
db_name = input("Database name: ").strip() or "databricks_postgres"

w.secrets.put_secret(
    scope="database",
    key="lakebase-database",
    string_value=db_name
)
print(f"✓ Stored database name: {db_name}")

# Set ACL permissions
w.secrets.put_acl(
    scope="database",
    principal="users",
    permission=workspace.AclPermission.READ,
)
print("✓ Set permissions for 'users' group")
print("\n✅ Setup complete! Your app can now connect to Lakebase using OAuth tokens.")
