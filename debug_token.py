#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

# Check current settings
from app.core.settings import settings
from app.core.security import create_access_token, decode_token

print("=== Current JWT Settings ===")
print(f"JWT_SECRET: {settings.jwt_secret}")
print(f"JWT_ALGORITHM: {settings.jwt_algorithm}")
print()

# Test token creation and decoding
print("=== Test Token Creation/Decoding ===")
test_token = create_access_token(subject="1")
print(f"Created token: {test_token[:50]}...")

try:
    decoded = decode_token(test_token)
    print(f"Decoded payload: {decoded}")
    print("✓ Token decoding successful")
except Exception as e:
    print(f"✗ Token decode failed: {e}")

# Test with database user
print("\n=== Test Database Query ===")
from app.db.session import SessionLocal
from app.db.models import User

s = SessionLocal()
user = s.query(User).filter(User.email == '123@gmail.com').first()
if user:
    print(f"✓ User found: ID={user.id}, Email={user.email}")
    
    # Try creating token for this user
    token = create_access_token(subject=str(user.id))
    print(f"Created token for user {user.id}: {token[:50]}...")
    
    # Try decoding
    try:
        payload = decode_token(token)
        print(f"✓ Token decoded: {payload}")
    except Exception as e:
        print(f"✗ Decode failed: {e}")
else:
    print("✗ User 123@gmail.com not found in database")

s.close()
