#!/bin/bash
# Frontend & Application Verification Script

echo "=== Finance App Verification ==="
echo ""

echo "1. Checking Docker containers..."
docker compose -f deploy/docker-compose.yml ps
echo ""

echo "2. Testing health endpoint..."
curl -s http://localhost:8000/health | jq . || curl -s http://localhost:8000/health
echo ""

echo "3. Testing root URL (should return HTML with React app)..."
curl -s http://localhost:8000/ | head -20
echo ""

echo "4. Checking if static files exist..."
docker compose -f deploy/docker-compose.yml exec web ls -lh /app/backend/finance_project/static/
echo ""

echo "5. Testing API endpoints..."
echo "Analytics Overview:"
curl -s http://localhost:8000/api/analytics/overview | jq . || curl -s http://localhost:8000/api/analytics/overview
echo ""

echo "6. Testing API docs..."
curl -s -I http://localhost:8000/api/docs/ | grep -E "HTTP|Content-Type"
echo ""

echo "=== Verification Complete ==="
echo ""
echo "✅ Application should be accessible at: http://localhost:8000"
echo "✅ API Documentation at: http://localhost:8000/api/docs/"
echo "✅ Admin Panel at: http://localhost:8000/admin/"

