# Lakebase OAuth Authentication Setup

## What Changed

Your app has been updated to use **OAuth tokens** for Lakebase authentication instead of static passwords. This is more secure and follows Databricks best practices.

## Why the "no password supplied" Error Occurred

The original code expected a full PostgreSQL connection URL with a password:
```
postgresql://user:password@host:5432/database
```

But the stored secret only had the URL without authentication credentials.

## How OAuth Tokens Work

1. The app now generates **temporary OAuth tokens** (valid for 1 hour) using the Databricks SDK
2. Tokens are automatically generated fresh on each connection
3. No need to manage static passwords

## Setup Steps

### Step 1: Find Your Lakebase Endpoint

Run the helper script to see your Lakebase projects and endpoints:

```bash
python list_lakebase_info.py
```

This will show you the **endpoint resource name** in this format:
```
projects/<project_id>/branches/<branch_id>/endpoints/<endpoint_id>
```

### Step 2: Store the Endpoint in Secrets

Run the updated setup script:

```bash
python setup_secrets.py
```

When prompted:
1. **Endpoint name**: Paste the full resource name from Step 1 (e.g., `projects/my-app/branches/production/endpoints/primary`)
2. **Database name**: Press Enter to use default `databricks_postgres`, or enter your database name

### Step 3: Redeploy Your App

After storing the secrets, redeploy your app:

```bash
databricks apps deploy <your-app-name>
```

## What Was Updated

1. **lakebase.py**: 
   - Now uses `w.postgres.generate_database_credential()` to generate OAuth tokens
   - Automatically fetches endpoint host from the SDK
   - Tokens are regenerated on each connection (valid for 1 hour)

2. **setup_secrets.py**:
   - Stores `lakebase-endpoint` (resource name) instead of full URL
   - Stores `lakebase-database` (database name)
   - Provides clear prompts and validation

3. **requirements.txt**:
   - Updated `databricks-sdk>=0.118.0` (required for postgres API)

## Troubleshooting

### "Permission denied for schema" error
- This means the schema is owned by a different role
- **Always deploy the app first** before running locally
- The app's Service Principal needs to create the schema to own it

### "Endpoint not found" error
- Double-check the endpoint resource name format
- Make sure you copied the full path: `projects/.../branches/.../endpoints/...`

### Token expired during long operations
- Tokens are valid for 1 hour
- The connection helper automatically generates fresh tokens
- For long-running operations, connections are recycled every 45 minutes

## Benefits of OAuth Tokens

✅ **More secure**: Tokens expire after 1 hour (vs. permanent passwords)
✅ **No password management**: No need to rotate or store static passwords
✅ **Better for production**: Recommended approach for Databricks Apps
✅ **Automatic refresh**: Fresh tokens on each connection
