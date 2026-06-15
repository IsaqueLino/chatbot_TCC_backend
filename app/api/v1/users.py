from fastapi import APIRouter, Depends
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserRead
from app.services.user import get_user_profile

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return await get_user_profile(current_user)