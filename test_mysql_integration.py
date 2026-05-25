import requests
import time
import sys

time.sleep(1)
try:
    r = requests.post('http://127.0.0.1:8000/auth/login', json={'email':'123@gmail.com','password':'12345678'}, timeout=5)
    print('Login status code:', r.status_code)
    
    if r.status_code == 200:
        token = r.json().get('access_token')
        print('✓ Login successful, token acquired')
        
        # Test query with token
        headers = {'Authorization': f'Bearer {token}'}
        query = {
            'query_text': 'Can I eat nasi lemak with diabetes?',
            'selected_food': 'nasi lemak',
            'portion': 'medium'
        }
        q = requests.post('http://127.0.0.1:8000/diet/query', json=query, headers=headers, timeout=30)
        print('Query status code:', q.status_code)
        
        if q.status_code == 200:
            result = q.json()
            print('✓ Query successful')
            print('Answer:', result.get('formatted_answer', 'NO ANSWER')[:100])
            
            # Verify query was saved to MySQL
            h = requests.get('http://127.0.0.1:8000/diet/history', headers=headers, timeout=5)
            print('History status:', h.status_code)
            if h.status_code == 200:
                history = h.json()
                print(f'✓ Query history retrieved: {len(history)} queries in MySQL')
        else:
            print('Query error:', q.text[:200])
    else:
        print('Login error:', r.text[:200])
        
except Exception as e:
    print('Exception:', type(e).__name__, str(e))
    sys.exit(1)
