#!/usr/bin/env python3
import requests
import time
import json

time.sleep(1)

print("=== Testing Full RAG Flow ===\n")

# 1. Login
print("1. Testing login...")
r = requests.post('http://127.0.0.1:8000/auth/login', 
                 json={'email':'123@gmail.com','password':'12345678'})
print(f"   Status: {r.status_code}")

if r.status_code != 200:
    print(f"   Error: {r.json()}")
    exit(1)

token = r.json().get('access_token')
print(f"   ✓ Token received: {token[:30]}...")

# 2. Test /auth/me to verify token works
print("\n2. Testing token with /auth/me...")
headers = {'Authorization': f'Bearer {token}'}
me = requests.get('http://127.0.0.1:8000/auth/me', headers=headers)
print(f"   Status: {me.status_code}")
if me.status_code == 200:
    print(f"   ✓ User: {me.json()['email']}")
else:
    print(f"   Error: {me.json()}")

# 3. Test /diet/foods (public)
print("\n3. Testing /diet/foods (no auth needed)...")
foods = requests.get('http://127.0.0.1:8000/diet/foods')
print(f"   Status: {foods.status_code}")
if foods.status_code == 200:
    foods_list = foods.json()
    print(f"   ✓ Foods loaded: {len(foods_list)} items")
else:
    print(f"   Error: {foods.json()}")

# 4. Test RAG query (needs auth + Ollama)
print("\n4. Testing /diet/query (RAG with Ollama)...")
query_payload = {
    'query_text': 'Can I eat nasi lemak with diabetes?',
    'selected_food': 'nasi lemak',
    'portion': 'medium'
}
q = requests.post('http://127.0.0.1:8000/diet/query', 
                 json=query_payload, 
                 headers=headers,
                 timeout=60)
print(f"   Status: {q.status_code}")

if q.status_code == 200:
    result = q.json()
    print(f"   ✓ Query succeeded")
    print(f"   Answer (first 100 chars): {result['formatted_answer'][:100]}")
    print(f"   References: {len(result['references'])} items")
else:
    print(f"   Error: {q.json()}")
    print(f"   Response: {q.text[:200]}")

# 5. Test history
print("\n5. Testing /diet/history...")
hist = requests.get('http://127.0.0.1:8000/diet/history', headers=headers)
print(f"   Status: {hist.status_code}")
if hist.status_code == 200:
    history = hist.json()
    print(f"   ✓ History loaded: {len(history)} queries")
else:
    print(f"   Error: {hist.json()}")

print("\n=== All tests completed ===")
