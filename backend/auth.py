"""
Authentication module for Dependify backend.
Handles GitHub OAuth and JWT token management.
"""
import jwt
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import Config

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})

        if not Config.API_SECRET_KEY:
            raise ValueError("API_SECRET_KEY not configured")

        encoded_jwt = jwt.encode(to_encode, Config.API_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token data

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, Config.API_SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    async def exchange_github_code(code: str) -> Dict:
        """
        Exchange GitHub OAuth code for access token.

        Args:
            code: OAuth code from GitHub

        Returns:
            GitHub access token and user info
        """
        if not Config.GITHUB_CLIENT_ID or not Config.GITHUB_CLIENT_SECRET:
            raise HTTPException(
                status_code=500,
                detail="GitHub OAuth not configured"
            )

        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": Config.GITHUB_CLIENT_ID,
                    "client_secret": Config.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )

            token_data = token_response.json()

            if "error" in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"GitHub OAuth error: {token_data.get('error_description', 'Unknown error')}"
                )

            access_token = token_data.get("access_token")

            # Get user information
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

            user_data = user_response.json()

            return {
                "github_token": access_token,
                "user": {
                    "id": user_data.get("id"),
                    "login": user_data.get("login"),
                    "name": user_data.get("name"),
                    "email": user_data.get("email"),
                    "avatar_url": user_data.get("avatar_url"),
                },
            }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User data from token

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = AuthService.verify_token(token)

    if "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    return payload


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict]:
    """
    Dependency to optionally get current user if authenticated.

    Args:
        authorization: Optional authorization header

    Returns:
        User data if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        payload = AuthService.verify_token(token)
        return payload
    except:
        return None


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Simple API key verification (for webhook endpoints).

    Args:
        x_api_key: API key from header

    Returns:
        True if valid

    Raises:
        HTTPException: If API key is invalid
    """
    # For now, accept any request without API key
    # In production, you should implement proper API key management
    return True
