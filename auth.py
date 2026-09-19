from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from database import get_db
from sqlalchemy.orm import Session
from typing import Annotated
from models import User
from schemas import (
    Token,
    NewUser,
    VerifyEmail,
    VerifyCode,
    ResetPassword,
    ForgetPassword
)
from email_verify import send_verification_email, send_reset_email

import jwt
import secrets
import os

from jwt.exceptions import PyJWTError
from datetime import datetime, timedelta, timezone


load_dotenv()


router = APIRouter(prefix="/auth", tags=["auth"])

secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")

if not secret_key:
    raise RuntimeError("SECRET_KEY is not configured")

if not algorithm:
    raise RuntimeError("ALGORITHM is not configured")

cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

MAX_OTP_ATTEMPTS = 5

o2auth_bearer = OAuth2PasswordBearer(
    tokenUrl="/auth/user-login"
)

db_dependency = Annotated[Session, Depends(get_db)]

def create_token(
    username: str,
    extra_time: timedelta,
    token_type: str,
    session: int
):
    expire = datetime.now(timezone.utc) + extra_time

    encode = {
        "sub": username,
        "type": token_type,
        "token_version": session,
        "exp": expire
    }

    return jwt.encode(
        encode,
        secret_key,
        algorithm=algorithm
    )

def set_refresh_cookie(
    response: Response,
    refresh_token: str
):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )

@router.post(
    "/user-signup",
    status_code=status.HTTP_201_CREATED
)
async def create_account(
    user: NewUser,
    db: db_dependency
):
    # Check email
    existing_email = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    existing_username = (
        db.query(User)
        .filter(User.username == user.username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    verification_code = f"{secrets.randbelow(1_000_000):06d}"

    verification_code_hash = ph.hash(verification_code)

    verification_expiry = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    )

    verification_id = secrets.token_urlsafe(32)

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=ph.hash(user.password),
        email_verified=False,

        verification_code=verification_code_hash,
        verification_code_expiry=verification_expiry,
        verification_id=verification_id,

        verification_attempts=0
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        await send_verification_email(
            user.email,
            verification_code
        )

    except Exception:
        db.delete(new_user)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not send verification email"
        )

    return {
        "message": "Account created successfully. Please verify your email",
        "Verification_id": verification_id
    }

@router.post("/email-verify")
async def verify(
    verify: VerifyEmail,
    db: db_dependency,
    response: Response
):
    user = (
        db.query(User)
        .filter(User.verification_id == verify.verification_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid verification request"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    if (
        user.verification_code_expiry is None
        or user.verification_code_expiry < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )

    if user.verification_attempts >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new verification code."
        )

    try:
        ph.verify(
            user.verification_code,
            verify.code
        )

    except (VerifyMismatchError, VerificationError):
        user.verification_attempts += 1
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    user.email_verified = True
    user.verification_code = None
    user.verification_code_expiry = None
    user.verification_id = None
    user.verification_attempts = 0

    db.commit()

    access_token = create_token(
        user.username,
        timedelta(minutes=10),
        "access_token",
        user.token_session
    )

    refresh_token = create_token(
        user.username,
        timedelta(days=7),
        "refresh_token",
        user.token_session
    )

    set_refresh_cookie(
        response,
        refresh_token
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post(
    "/user-login",
    response_model=Token
)
async def login(
    data_form: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    db: db_dependency,
    response: Response
):
    user = authenticate(
        data_form.username,
        data_form.password,
        db
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )

    access_token = create_token(
        user.username,
        timedelta(minutes=10),
        "access_token",
        user.token_session
    )

    refresh_token = create_token(
        user.username,
        timedelta(days=7),
        "refresh_token",
        user.token_session
    )

    set_refresh_cookie(
        response,
        refresh_token
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    
@router.post(
    "/refresh-token",
    response_model=Token
)
async def refresh_token(
    request: Request,
    db: db_dependency
):
    refresh_token_value = request.cookies.get(
        "refresh_token"
    )

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    try:
        payload = jwt.decode(
            refresh_token_value,
            secret_key,
            algorithms=[algorithm]
        )

        username = payload.get("sub")
        token_type = payload.get("type")
        session = payload.get("token_version")

        if (
            username is None
            or token_type != "refresh_token"
            or session is None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if session != user.token_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    token = create_token(
        user.username,
        timedelta(minutes=20),
        "access_token",
        user.token_session
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def authenticate(
    username: str,
    password: str,
    db: db_dependency
):
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        return None

    try:
        ph.verify(
            user.hashed_password,
            password
        )

        if ph.check_needs_rehash(user.hashed_password):
            user.hashed_password = ph.hash(password)
            db.commit()

        return user

    except (VerifyMismatchError, VerificationError):
        return None

def get_current_user(
    token: Annotated[
        str,
        Depends(o2auth_bearer)
    ],
    db: db_dependency
):
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm]
        )

        username = payload.get("sub")
        token_type = payload.get("type")
        session = payload.get("token_version")

        if (
            username is None
            or session is None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if token_type != "access_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"}
            )

    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if session != user.token_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user

@router.post("/forgot-password")
async def forget_password(
    email: ForgetPassword,
    db: db_dependency
):
    user = (
        db.query(User)
        .filter(User.email == email.email)
        .first()
    )

    if user is None or not user.email_verified:
        return {"message": "If the account exists, a reset code has been sent."}

    # Generate plaintext code
    reset_code = f"{secrets.randbelow(1_000_000):06d}"
    reset_code_hash = ph.hash(reset_code)
    
    reset_code_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    reset_id = secrets.token_urlsafe(32)

    user.reset_code = reset_code_hash
    user.reset_code_expiry = reset_code_expiry
    user.reset_id = reset_id
    user.reset_attempts = 0

    db.commit()

    try:
        # Send plaintext code to the user
        await send_reset_email(
            email.email,
            reset_code
        )

    except Exception:
        user.reset_code = None
        user.reset_code_expiry = None
        user.reset_id = None
        user.reset_attempts = 0

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not send reset code"
        )

    return {
        "message": "If the account exists, a reset code has been sent.",
        "reset_id": reset_id
    }

@router.post("/verify-reset-code")
async def verify_code(
    data: VerifyCode,
    db: db_dependency
):
    user = (
        db.query(User)
        .filter(User.reset_id == data.reset_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid reset request"
        )

    if (
        user.reset_code_expiry is None
        or user.reset_code_expiry < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired"
        )

    if user.reset_attempts >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new reset code."
        )

    try:
        ph.verify(
            user.reset_code,
            data.code
        )

    except (VerifyMismatchError, VerificationError):
        user.reset_attempts += 1
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code"
        )

    reset_token = create_token(
        user.username,
        timedelta(minutes=5),
        "reset_token",
        user.token_session
    )
    user.reset_code = None
    user.reset_id = None
    user.reset_code_expiry = None
    user.reset_attempts = 0

    db.commit()

    return {
        "reset_token": reset_token,
        "token_type": "bearer"
    }

@router.post("/reset-password")
async def reset_password(
    data: ResetPassword,
    db: db_dependency
):
    try:
        payload = jwt.decode(
            data.reset_token,
            secret_key,
            algorithms=[algorithm]
        )

        username = payload.get("sub")
        token_type = payload.get("type")
        session = payload.get("token_version")

        if (
            username is None
            or token_type != "reset_token"
            or session is None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid reset token"
            )

    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token"
        )

    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token"
        )

    if session != user.token_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    user.hashed_password = ph.hash(
        data.new_password
    )

    user.token_session += 1

    db.commit()

    return {
        "message": "Password reset successfully"
    }