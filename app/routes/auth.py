from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import create_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.deps import check_rate_limit
from app.models import School, SessionToken, User
from app.schemas import LoginIn, SignupIn, TokenOut, UserOut

router = APIRouter(prefix='/auth', tags=['auth'])


def _extract_domain(email: str) -> str:
    return email.split('@')[-1].lower()


@router.post('/signup', response_model=UserOut, status_code=201)
def signup(payload: SignupIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request)
    allowed_domains = {d.strip().lower() for d in settings.allowed_school_domains.split(',') if d.strip()}
    domain = _extract_domain(payload.email)
    if domain not in allowed_domains:
        raise HTTPException(status_code=400, detail='Email domain is not allowed')

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail='Email already in use')

    school = db.query(School).filter(School.domain == domain).first()
    if not school:
        school = School(name=domain.split('.')[0].title(), domain=domain)
        db.add(school)
        db.flush()

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        school_id=school.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post('/login', response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request)
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    token, expires_at = create_token(str(user.id))
    db.add(SessionToken(user_id=user.id, token=token, expires_at=expires_at))
    db.commit()
    return TokenOut(access_token=token)
