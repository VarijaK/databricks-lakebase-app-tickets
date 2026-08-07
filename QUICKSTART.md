# Quick Start Guide - Testing Locally

## Prerequisites

Before you start, make sure you have:
1. Python 3.8 or higher installed
2. A Lakebase instance created in your Databricks workspace
3. The Lakebase connection URL (from your Lakebase instance setup)

## Step 1: Install Dependencies

```bash
cd databricks-lakebase-app-tickets
pip install -r requirements.txt
```

## Step 2: Configure Environment

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your Lakebase connection URL:

```bash
# Replace with your actual Lakebase URL
LAKEBASE_URL=postgresql://your_role:your_password@your-host.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require
```

**Note:** Your Lakebase URL should look like this:
- Host: `*.database.cloud.databricks.com`
- Port: `5432`
- Database: `databricks_postgres`
- SSL: `sslmode=require`

Get this URL from your Lakebase instance in the Databricks Catalog UI.

## Step 3: Start the App

```bash
python app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://0.0.0.0:8000
```

## Step 4: Test the API

### Option A: Use the Test Script (Recommended)

In a new terminal, run:

```bash
python test_local.py
```

This will automatically test all endpoints and show you the results.

### Option B: Manual Testing with curl

**1. Health check:**
```bash
curl http://localhost:8000/healthz
```

**2. Create a ticket:**
```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"title": "Database connection timeout", "status": "open"}'
```

**3. List all tickets:**
```bash
curl http://localhost:8000/tickets
```

**4. Get a specific ticket (replace {id} with actual ticket_id):**
```bash
curl http://localhost:8000/tickets/1
```

**5. Add a message to a ticket:**
```bash
curl -X POST http://localhost:8000/tickets/1/messages \
  -H "Content-Type: application/json" \
  -d '{"message_text": "I am investigating this issue"}'
```

**6. Update ticket status:**
```bash
curl -X PUT http://localhost:8000/tickets/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**7. Delete a ticket:**
```bash
curl -X DELETE http://localhost:8000/tickets/1
```

## Troubleshooting

### Connection Error
If you get a connection error, check:
- Is your Lakebase instance running?
- Is the LAKEBASE_URL correct in your .env file?
- Can you connect to your Lakebase instance from your network?

### Import Error
If you get import errors, make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Authentication Error
For local testing, the app will use your Databricks CLI authentication.
Make sure you're authenticated:
```bash
databricks auth login --host https://your-workspace.cloud.databricks.com
```

## Next Steps

Once local testing works:
1. Commit your code to a Git repository
2. Create a Git folder in Databricks pointing to your repo
3. Deploy as a Databricks App (see README.md for full deployment instructions)

## Database Schema

The app automatically creates these tables on first run:

**tickets**
- ticket_id (SERIAL PRIMARY KEY)
- title (TEXT)
- status (TEXT) - values: open, in_progress, resolved, closed
- created_by (TEXT) - user email
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)

**ticket_messages**
- message_id (SERIAL PRIMARY KEY)
- ticket_id (INTEGER, foreign key)
- message_text (TEXT)
- author (TEXT) - user email
- created_at (TIMESTAMPTZ)
