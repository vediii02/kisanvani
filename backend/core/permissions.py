from fastapi import Depends, HTTPException, status
from typing import List
from db.models.user import User
from core.auth import get_current_user


def require_role(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        print(current_user,"current user in permission--------------------------------------")
        current_user_role = current_user["role"]
        print(current_user_role,"current user role in permission--------------------------------------")    
        if current_user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user
    return role_checker