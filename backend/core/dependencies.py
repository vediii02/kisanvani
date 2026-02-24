from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
import os

from db.session import get_db
from db.models.user import User

SECRET_KEY = os.getenv("SECRET_KEY", "kisanvani-secret-key-change-in-production")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or invalid user",
        )

    return user


async def get_organisation_admin(
    current_user: User = Depends(get_current_active_user),
):
    """Verify user is organisation admin"""
    if current_user.role not in ["organisation_admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organisation admin access required",
        )
    return current_user


async def get_current_organisation_admin(
    current_user: User = Depends(get_current_active_user),
):
    """Verify user is organisation admin, organisation, or company (all can manage org data)"""
    if current_user.role not in ["organisation_admin", "organisation", "company"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organisation or company access required",
        )
    if not current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not linked to any organisation",
        )
    return current_user
