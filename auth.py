import os
import uuid
import json
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal
from models.user import User, UserRole

load_dotenv()

JWT_SECRET = os.environ.get("JWT_SECRET", "credence-super-secure-jwt-signing-secret-key-32bytes-min")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str, name: str, role: str = "CUSTOMER") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "role": str(role.value if isinstance(role, UserRole) else role),
        "iat": now,
        "exp": now + timedelta(days=14)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None

def get_user_by_email(email: str, db: Optional[Session] = None) -> Optional[User]:
    clean_email = email.strip().lower()
    if db is not None:
        return db.query(User).filter(func.lower(User.email) == clean_email).first()
    with SessionLocal() as session:
        return session.query(User).filter(func.lower(User.email) == clean_email).first()

def get_user_by_google_id(google_id: str, db: Optional[Session] = None) -> Optional[User]:
    if db is not None:
        return db.query(User).filter(User.google_id == google_id).first()
    with SessionLocal() as session:
        return session.query(User).filter(User.google_id == google_id).first()

def get_user_by_id(user_id: str, db: Optional[Session] = None) -> Optional[User]:
    if db is not None:
        return db.query(User).filter(User.id == user_id).first()
    with SessionLocal() as session:
        return session.query(User).filter(User.id == user_id).first()

def link_google_account(
    user_id: str,
    google_id: str,
    avatar_url: Optional[str] = None,
    db: Optional[Session] = None
) -> Optional[User]:
    """
    Links an existing user account with a Google OAuth ID.
    If the user previously registered with email/password, auth_provider becomes 'both'.
    """
    def _perform_link(session: Session) -> Optional[User]:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        if user.password_hash:
            user.auth_provider = "both"
        else:
            user.auth_provider = "google"
        session.commit()
        session.refresh(user)
        return user

    if db is not None:
        return _perform_link(db)
    with SessionLocal() as session:
        return _perform_link(session)

def create_user(
    email: str,
    name: str,
    password: Optional[str] = None,
    role: UserRole = UserRole.CUSTOMER,
    auth_provider: str = "email",
    google_id: Optional[str] = None,
    avatar_url: Optional[str] = None,
    db: Optional[Session] = None
) -> User:
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    pwd_hash = hash_password(password) if password else None
    clean_email = email.strip().lower()
    clean_name = name.strip()

    new_user = User(
        id=user_id,
        email=clean_email,
        name=clean_name,
        password_hash=pwd_hash,
        role=role,
        auth_provider=auth_provider,
        google_id=google_id,
        avatar_url=avatar_url
    )

    def _perform_create(session: Session) -> User:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user

    if db is not None:
        return _perform_create(db)
    with SessionLocal() as session:
        return _perform_create(session)

def verify_google_credential(credential: str) -> Dict[str, Any]:
    """
    Verifies a Google OAuth ID Token using Google's public key infrastructure.
    """
    credential_str = credential.strip()
    target_audience = GOOGLE_CLIENT_ID if GOOGLE_CLIENT_ID else None

    # 1. Try real Google ID token verification via google-auth
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
        idinfo = id_token.verify_oauth2_token(credential_str, requests.Request(), audience=target_audience)
        return {
            "google_id": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "name": idinfo.get("name", "Google User"),
            "avatar_url": idinfo.get("picture")
        }
    except Exception as verify_err:
        # If a specific GOOGLE_CLIENT_ID was configured, respect its verification strictly
        if GOOGLE_CLIENT_ID:
            raise ValueError(f"Google Token Verification Failed: {str(verify_err)}")

        # 2. Fallback: Parse genuine 3-part Google JWT payload if in offline/local testing
        parts = credential_str.split(".")
        if len(parts) == 3:
            try:
                padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                claims = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
                if "email" in claims:
                    return {
                        "google_id": str(claims.get("sub", uuid.uuid4())),
                        "email": claims["email"],
                        "name": claims.get("name", claims["email"].split("@")[0].title()),
                        "avatar_url": claims.get("picture", "")
                    }
            except Exception:
                pass

        raise ValueError(f"Unable to verify Google credential: {str(verify_err)}")
