"""
Helper script to list your Lakebase projects and endpoints.
Run this to find the endpoint resource name you need for setup_secrets.py

Usage:
    python list_lakebase_info.py
"""
from databricks.sdk import WorkspaceClient
import itertools

w = WorkspaceClient()

print("=" * 80)
print("LAKEBASE PROJECTS AND ENDPOINTS")
print("=" * 80)

try:
    # List all projects (limit to first 10)
    projects = list(itertools.islice(w.postgres.list_projects(page_size=10), 10))
    
    if not projects:
        print("\n⚠️  No Lakebase projects found in this workspace.")
        print("\nTo create one, visit: https://docs.databricks.com/aws/en/oltp/projects/")
    else:
        for project in projects:
            display = project.spec.display_name if project.spec else project.name
            print(f"\n📦 Project: {display}")
            print(f"   Resource name: {project.name}")
            
            # List branches for this project
            branches = list(w.postgres.list_branches(parent=project.name))
            for branch in branches:
                print(f"\n  🌿 Branch: {branch.name.split('/')[-1]}")
                print(f"     State: {branch.status.current_state}")
                
                # List endpoints for this branch
                endpoints = list(w.postgres.list_endpoints(parent=branch.name))
                for endpoint in endpoints:
                    endpoint_id = endpoint.name.split('/')[-1]
                    state = endpoint.status.current_state
                    host = endpoint.status.hosts.host if endpoint.status.hosts else "N/A"
                    
                    print(f"\n    🔌 Endpoint: {endpoint_id}")
                    print(f"       Full resource name: {endpoint.name}")
                    print(f"       State: {state}")
                    print(f"       Host: {host}")
                    
                    print(f"\n       💡 Use this for setup_secrets.py:")
                    print(f"          {endpoint.name}")
                
                # List databases for this branch
                databases = list(w.postgres.list_databases(parent=branch.name))
                if databases:
                    print(f"\n    📊 Databases:")
                    for db in databases:
                        db_name = db.name.split('/')[-1]
                        print(f"       - {db_name}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure you have:")
    print("  1. databricks-sdk >= 0.118.0 installed")
    print("  2. Permissions to access Lakebase projects")

print("\n" + "=" * 80)
