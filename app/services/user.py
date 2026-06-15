from app.models.user import User
from app.schemas.user import UserRead

async def get_user_profile(user: User) -> UserRead:
    return UserRead.model_validate(user)