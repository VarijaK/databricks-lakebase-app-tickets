"""
Update Lakebase secrets for OAuth authentication.
Run this script to configure your app with the correct endpoint.
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Configuration for the "tickets" project
ENDPOINT_NAME = "projects/tickets/branches/production/endpoints/primary"
DATABASE_NAME = "databricks_postgres"  # Note: underscore, not hyphen!

print("=" * 80)
print("UPDATING SECRETS FOR LAKEBASE OAUTH AUTHENTICATION")
print("=" * 80)

# Store endpoint secret
print(f"\n1. Storing endpoint: {ENDPOINT_NAME}")
w.secrets.put_secret(
    scope="database",
    key="lakebase-endpoint",
    string_value=ENDPOINT_NAME
)
print("   ✓ Stored 'lakebase-endpoint' secret")

# Store database name
print(f"\n2. Storing database: {DATABASE_NAME}")
w.secrets.put_secret(
    scope="database",
    key="lakebase-database",
    string_value=DATABASE_NAME
)
print("   ✓ Stored 'lakebase-database' secret")

# Verify
print("\n3. Current secrets in 'database' scope:")
secrets = [s.key for s in w.secrets.list_secrets(scope='database')]
for key in sorted(secrets):
    print(f"   • {key}")

print("\n" + "=" * 80)
print("✅ SECRETS CONFIGURED!")
print("=" * 80)
print(f"\nEndpoint: {ENDPOINT_NAME}")
print(f"Database: {DATABASE_NAME}")
print(f"Host: ep-billowing-sky-d8kjj352.database.us-east-2.cloud.databricks.com")
print("\nNext: Redeploy your app with 'databricks apps deploy lakebase-app-tickets'")
