#!/bin/bash
# Test script to verify scheduler is working

echo "=========================================="
echo "Scheduler Status Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if server is running
echo "1. Checking if Flask server is running..."
if curl -s http://localhost:5001/api/scheduler/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not running. Start it with: python run.py${NC}"
    exit 1
fi

echo ""
echo "2. Getting scheduler status..."
echo "----------------------------------------"

# Get full status
response=$(curl -s http://localhost:5001/api/scheduler/status)

# Pretty print the response
echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

echo ""
echo "----------------------------------------"

# Parse and display key info
enabled=$(echo "$response" | grep -o '"enabled":[^,}]*' | cut -d':' -f2)
running=$(echo "$response" | grep -o '"running":[^,}]*' | cut -d':' -f2)
training_count=$(echo "$response" | grep -o '"training_count":[^,}]*' | cut -d':' -f2)
total_labels=$(echo "$response" | grep -o '"total_labels":[^,}]*' | cut -d':' -f2)

echo ""
echo "Summary:"
echo "--------"

if [ "$enabled" = "true" ] || [ "$enabled" = " true" ]; then
    echo -e "${GREEN}✓ Scheduler is ENABLED${NC}"
else
    echo -e "${YELLOW}⚠ Scheduler is DISABLED${NC}"
    echo -e "  To enable: Set ENABLE_SCHEDULER=true in backend/app/config/.env"
fi

if [ "$running" = "true" ] || [ "$running" = " true" ]; then
    echo -e "${GREEN}✓ Scheduler is RUNNING${NC}"
else
    echo -e "${RED}✗ Scheduler is NOT running${NC}"
fi

echo "  Training runs completed: ${training_count:-0}"
echo "  Labeled data in database: ${total_labels:-0}"

echo ""
echo "=========================================="
