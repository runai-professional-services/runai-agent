#!/bin/bash
# Test script to verify automatic database creation

set -e

echo "🧪 Testing Failure Database Auto-Creation"
echo "=========================================="
echo ""

# Clean up any existing test database
TEST_DB="/tmp/test_runai_failure_db_$(date +%s).db"
echo "📝 Test database path: $TEST_DB"
echo ""

# Activate virtual environment if it exists
if [ -d "runai-agent/.venv" ]; then
    echo "🔧 Activating virtual environment..."
    source runai-agent/.venv/bin/activate
fi

# Create a simple test script
TEST_SCRIPT=$(mktemp)
cat > "$TEST_SCRIPT" << 'EOF'
import sys
import os
sys.path.insert(0, 'runai-agent/src')

from runai_agent.functions.failure_analyzer import FailureDatabase

# Database path from command line
db_path = sys.argv[1]

print("1️⃣ Attempting to create FailureDatabase instance...")
print(f"   Path: {db_path}")
print("")

# Check that file doesn't exist yet
if os.path.exists(db_path):
    print(f"❌ ERROR: Database file already exists at {db_path}")
    sys.exit(1)

print("✅ Confirmed: Database file does not exist yet")
print("")

# Initialize database (should auto-create)
print("2️⃣ Initializing database...")
db = FailureDatabase(db_path)
print("")

# Verify file was created
if os.path.exists(db_path):
    print("✅ SUCCESS: Database file created automatically!")
    print(f"   Path: {db_path}")
    
    # Get file size
    size = os.path.getsize(db_path)
    print(f"   Size: {size} bytes")
else:
    print(f"❌ ERROR: Database file was not created at {db_path}")
    sys.exit(1)

print("")
print("3️⃣ Testing database operations...")

# Record a test failure
failure_data = {
    'project': 'test-project',
    'job_name': 'test-job',
    'failure_type': 'OOMKilled',
    'phase': 'Failed',
    'error_message': 'Out of memory',
    'pod_name': 'test-pod',
    'node_name': 'test-node',
    'container_image': 'pytorch:2.0',
    'logs_snippet': 'Test log snippet',
    'events_snippet': 'Test events',
    'gpu_count': 1,
    'memory_request': '8Gi',
    'cpu_request': '4'
}
db.record_failure(failure_data)

print("✅ Successfully recorded test failure")
print("")

# Retrieve statistics
stats = db.get_pattern_stats(days=7)
failure_count = len(db.get_recent_failures(days=7))
print(f"✅ Retrieved statistics: {failure_count} failures recorded")
print("")

print("🎉 All tests passed!")
print("")
print("Summary:")
print("--------")
print("✅ Database auto-created on first access")
print("✅ Schema initialized automatically")
print("✅ Write operations work correctly")
print("✅ Read operations work correctly")
print("")
print("This same process happens automatically when:")
print("  • Main agent starts and needs to query failures")
print("  • Monitoring sidecar starts and records failures")
print("  • No manual setup required!")
EOF

# Run the test
python3 "$TEST_SCRIPT" "$TEST_DB"

# Clean up
rm "$TEST_SCRIPT"
rm "$TEST_DB"

echo ""
echo "🧹 Cleaned up test database"
echo "✅ Test complete!"

