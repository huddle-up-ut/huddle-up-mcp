#!/bin/bash

echo "🧪 Testing MCP Agents..."

# Test Team Captain Agent
echo "Testing Team Captain Agent (Port 8001)..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Team Captain Agent is running"
else
    echo "❌ Team Captain Agent is not responding"
fi

# Test Schedule Agent
echo "Testing Schedule Agent (Port 8002)..."
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✅ Schedule Agent is running"
else
    echo "❌ Schedule Agent is not responding"
fi

# Test Attendance Agent
echo "Testing Attendance Agent (Port 8003)..."
if curl -s http://localhost:8003/health > /dev/null; then
    echo "✅ Attendance Agent is running"
else
    echo "❌ Attendance Agent is not responding"
fi

echo "🧪 Agent testing complete!" 