from __future__ import annotations

import json

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import firebase_admin
from firebase_admin import auth, credentials


from app.config import get_settings

security = HTTPBearer(auto_error=False)

settings = get_settings()

firebase_initialized = False

if not firebase_admin._apps:
    try:
        if settings.firebase_service_account_json:
            cred = credentials.Certificate(json.loads(settings.firebase_service_account_json))
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
        elif settings.firebase_credentials_path:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
        else:
            if settings.is_production:
                raise RuntimeError("Firebase credentials are required for authenticated routes")
            else:
                print("Warning: Firebase credentials not configured. Running in local guest mode.")
    except Exception as exc:
        if settings.is_production:
            raise
        else:
            print(f"Warning: Failed to load Firebase credentials ({exc}). Running in local guest mode.")


def is_local_request(request: Request) -> bool:
    if not request:
        return False
    hostname = request.url.hostname or ""
    return (
        hostname in {"localhost", "127.0.0.1", "::1"}
        or hostname.startswith("192.168.")
        or hostname.startswith("10.")
        or hostname.startswith("172.16.")
    )


async def get_current_user(
    request: Request = None,
    credentials_header: HTTPAuthorizationCredentials = Depends(security),
):
    settings = get_settings()
    is_local = not settings.is_production

    if not credentials_header:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization token",
        )

    token = credentials_header.credentials

    # Bypass Firebase verification in local environment if token is 'guest'
    if token == "guest" and (is_local or not firebase_initialized or is_local_request(request)):
        return {
            "uid": "guest",
            "email": "guest@example.com",
            "name": "Guest Player",
            "email_verified": True,
            "picture": None,
            "provider": "anonymous",
            "admin": True,
        }

    if not firebase_initialized:
        raise HTTPException(
            status_code=401,
            detail="Firebase is not initialized and token is not guest",
        )

    try:
        try:
            decoded_token = auth.verify_id_token(token)
        except Exception as exc:
            if "Token used too early" in str(exc):
                import asyncio
                import logging
                logging.getLogger("ai_story.auth").warning("Token used too early due to clock skew. Retrying in 1s...")
                await asyncio.sleep(1.0)
                decoded_token = auth.verify_id_token(token)
            else:
                raise

        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "email_verified": decoded_token.get("email_verified", False),
            "picture": decoded_token.get("picture"),
            "provider": decoded_token.get("firebase", {}).get("sign_in_provider"),
            "admin": decoded_token.get("admin") is True,
        }

    except Exception as exc:
        print("Firebase verify error:", repr(exc))

        raise HTTPException(
            status_code=401,
            detail=f"Invalid Firebase token: {str(exc)}",
        )


async def require_admin_user(user=Depends(get_current_user)):
    if not user.get("admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return user
