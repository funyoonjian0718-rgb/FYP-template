from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db

#tells fast APi the endpoint where 123@gmail.com and PASS gets the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

#function to retrieve the database + login token 
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)       #decode the token to get user id
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    user = db.scalar(select(User).where(User.id == user_id))     #got token but no user in database 
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

