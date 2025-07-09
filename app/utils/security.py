# app/utils/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import httpx
import json
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def base64url_decode(data: str) -> bytes:
    """Decode base64url-encoded data"""
    # Add padding if needed
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    # Replace URL-safe characters
    data = data.replace('-', '+').replace('_', '/')
    return base64.b64decode(data)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "token_type": "refresh"}) # Add token type
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def verify_clerk_jwt(token: str, check_expiration: bool = True) -> dict:
    """
    Verify a Clerk JWT token using their JWKS endpoint
    """
    try:
        # Fetch JWKS from Clerk
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.CLERK_JWKS_URL)
            response.raise_for_status()
            jwks = response.json()
        
        # Decode the token header to get the key ID
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header.get("kid")
        
        if not key_id:
            raise JWTError("No key ID found in token header")
        
        # Find the correct key in JWKS
        public_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == key_id:
                # Convert JWK to PEM format
                jwk_dict = {
                    "kty": key["kty"],
                    "n": key["n"],
                    "e": key["e"]
                }
                
                # Create RSA public key from JWK components
                n_bytes = base64url_decode(jwk_dict["n"])
                e_bytes = base64url_decode(jwk_dict["e"])
                
                n_int = int.from_bytes(n_bytes, 'big')
                e_int = int.from_bytes(e_bytes, 'big')
                
                public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
                public_key = public_numbers.public_key()
                break
        
        if not public_key:
            raise JWTError(f"No matching key found for key ID: {key_id}")
        
        # Convert public key to PEM format for jwt.decode
        pem_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Verify and decode the token
        decode_options = {
            "algorithms": ["RS256"],
            "audience": "https://project-guruji-new-smoky.vercel.app",  # Your Clerk application URL
            "issuer": "https://apt-flamingo-7.clerk.accounts.dev"  # Your Clerk issuer URL
        }
        
        if not check_expiration:
            decode_options["options"] = {"verify_exp": False}
        
        payload = jwt.decode(
            token,
            pem_public_key,
            **decode_options
        )
        
        return payload
        
    except httpx.RequestError as e:
        raise JWTError(f"Failed to fetch JWKS: {e}")
    except JWTError as e:
        raise e
    except Exception as e:
        raise JWTError(f"Token verification failed: {e}")