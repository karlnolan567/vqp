#!/bin/bash

# VQP Prototype - Test Runner Script
echo "------------------------------------------------"
echo "🚀 Starting VQP Rules Engine Unit Tests..."
echo "------------------------------------------------"

# Run pytest via python3 module to ensure path consistency
python3 -m pytest tests/ -v

# Capture the exit code of the test run
RESULT=$?

echo "------------------------------------------------"
if [ $RESULT -eq 0 ]; then
    echo "✅ SUCCESS: All tests passed boundaries and edge cases."
else
    echo "❌ FAILURE: One or more tests failed. Check the output above."
fi
echo "------------------------------------------------"

exit $RESULT
