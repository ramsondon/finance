#!/bin/bash

# Test script for recurring transactions API

echo "🧪 Testing Recurring Transactions API"
echo "======================================"
echo ""

# Test if server is running
echo "⏳ Waiting for server to be ready..."
sleep 5

echo "📍 Testing /health/ endpoint..."
curl -s http://localhost:8000/health/ | head -20 || echo "Server not ready"
echo ""
echo ""

echo "📍 Testing recurring transactions API..."
# Get list endpoint (should return 403 without auth, which is correct)
curl -s http://localhost:8000/api/banking/recurring/ | head -20
echo ""
echo ""

echo "📍 Testing summary endpoint..."
# Get summary endpoint (should return 403 without auth)
curl -s http://localhost:8000/api/banking/recurring/summary/ | head -20
echo ""
echo ""

echo "✅ Tests complete!"

