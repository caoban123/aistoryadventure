from __future__ import annotations

import json

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import firebase_admin
from firebase_admin import auth, credentials

from app.config import get_settings

security = HTTPBearer(auto_error=False)

settings = get_settings()

if not firebase_admin._apps:
    if settings.firebase_service_account_json:
        cred = credentials.Certificate(json.loads(settings.firebase_service_account_json))
    elif settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        raise RuntimeError("Firebase credentials are required for authenticated routes")

    firebase_admin.initialize_app(cred)


async def get_current_user(
    credentials_header: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials_header:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization token",
        )

    token = credentials_header.credentials

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
