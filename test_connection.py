"""
Test Lakebase connection with OAuth tokens.
Run this AFTER updating secrets to verify everything works.
"""
import sys
sys.path.insert(0, '/Workspace/Users/varija.karampudi@gmail.com/databricks-lakebase-app-tickets')

print("=" * 80)
print("TESTING LAKEBASE CONNECTION")
print("=" * 80)

# Test 1: Import lakebase module
print("\n1. Testing import...")
try:
    import lakebase
    print("   ✓ Successfully imported lakebase module")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")
    exit(1)

# Test 2: Get connection params
print("\n2. Testing connection parameters...")
try:
    params = lakebase._get_connection_params()
    print(f"   ✓ Host: {params['host']}")
    print(f"   ✓ Database: {params['dbname']}")
    print(f"   ✓ User: {params['user']}")
    print(f"   ✓ Token generated: {len(params['password'])} chars")
    print(f"   ✓ SSL mode: {params['sslmode']}")
except Exception as e:
    print(f"   ❌ Failed to get connection params: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Test actual connection
print("\n3. Testing database connection...")
try:
    result = lakebase.run_query("SELECT current_database(), current_user, version()")
    print(f"   ✓ Connection successful!")
    print(f"   ✓ Database: {result[0]['current_database']}")
    print(f"   ✓ User: {result[0]['current_user']}")
    print(f"   ✓ Version: {result[0]['version'][:50]}...")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Test table creation
print("\n4. Testing table operations...")
try:
    # Create test table
    lakebase.run_write("""
        CREATE TABLE IF NOT EXISTS test_connection (
            id SERIAL PRIMARY KEY,
            message TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    print("   ✓ Test table created")
    
    # Insert test data
    lakebase.run_write(
        "INSERT INTO test_connection (message) VALUES (%s)",
        ("Connection test successful!",)
    )
    print("   ✓ Test data inserted")
    
    # Query test data
    result = lakebase.run_query("SELECT * FROM test_connection ORDER BY id DESC LIMIT 1")
    print(f"   ✓ Test data retrieved: {result[0]['message']}")
    
    # Clean up
    lakebase.run_write("DROP TABLE test_connection")
    print("   ✓ Test table cleaned up")
    
except Exception as e:
    print(f"   ❌ Table operations failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print("\nYour Lakebase connection is working correctly.")
print("You can now deploy your app with confidence:")
print("  databricks apps deploy lakebase-app-tickets")
