from collections import defaultdict
from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import SessionToken, User

security = HTTPBearer()
RATE_BUCKETS: dict[str, list[datetime]] = defaultdict(list)


def check_rate_limit(request: Request):
    ip = request.client.host if request.client else 'unknown'
    now = datetime.utcnow()
    window_start = now.replace(second=0, microsecond=0)
    RATE_BUCKETS[ip] = [t for t in RATE_BUCKETS[ip] if t >= window_start]
    if len(RATE_BUCKETS[ip]) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail='Rate limit exceeded')
    RATE_BUCKETS[ip].append(now)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token subject')

    session = db.query(SessionToken).filter(
        SessionToken.token == token,
        SessionToken.expires_at > datetime.utcnow(),
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session expired')

    user = db.query(User).filter(User.id == int(user_id), User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user
