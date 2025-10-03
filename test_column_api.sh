#!/bin/bash
echo "🧪 Testing Column Mapping Configuration API"
echo "=========================================="

# Test 1: Validate a column
echo -e "\n1️⃣ Test: Validate column 'A'"
curl -s -X POST http://localhost:8000/api/v1/column-config/validate \
  -H "Content-Type: application/json" \
  -d '{"column": "A"}' | python3 -m json.tool

# Test 2: Validate invalid column
echo -e "\n2️⃣ Test: Validate invalid column 'AAA'"
curl -s -X POST http://localhost:8000/api/v1/column-config/validate \
  -H "Content-Type: application/json" \
  -d '{"column": "AAA"}' | python3 -m json.tool

# Test 3: Save column mappings (with session)
echo -e "\n3️⃣ Test: Save column mappings"
curl -s -X POST http://localhost:8000/api/v1/column-config \
  -H "Content-Type: application/json" \
  -H "session_id: test-session-123" \
  -d '{"date_column": "A", "description_column": "B", "price_column": "C"}' | python3 -m json.tool

# Test 4: Get column mappings
echo -e "\n4️⃣ Test: Get column mappings"
curl -s -X GET http://localhost:8000/api/v1/column-config \
  -H "session_id: test-session-123" | python3 -m json.tool

# Test 5: Test without auth
echo -e "\n5️⃣ Test: Get mappings without auth (should fail)"
curl -s -X GET http://localhost:8000/api/v1/column-config | python3 -m json.tool

echo -e "\n✅ API tests complete!"
