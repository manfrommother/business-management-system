from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
from typing import Optional

from app.core.config import settings

# This scheme expects the token to be sent in the Authorization header
# as 'Bearer <token>'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login") # Adjust tokenUrl if needed

class TokenData(BaseModel):
    user_id: Optional[int] = None
    # Add other fields potentially present in the token payload, e.g.:
    # company_id: Optional[int] = None
    # roles: List[str] = []

class AuthenticatedUser(BaseModel):
    id: int
    # Add other relevant user details derived from token or DB lookup
    # company_id: Optional[int] = None
    # roles: List[str] = []

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthenticatedUser:
    """Dependency to validate JWT token and return user data."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: Optional[int] = payload.get("user_id") # Adjust key based on User Service token
        if user_id is None:
            raise credentials_exception
        
        # You could fetch more user details from the DB here if needed
        # based on user_id, but for now, just return the ID.
        return AuthenticatedUser(id=user_id)
        
    except JWTError:
        raise credentials_exception
    except ValidationError: # If TokenData validation fails (though less likely here)
        raise credentials_exception 