from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, get_session
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UpdateProfileRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    user, token = await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        default_currency=body.default_currency,
    )
    return AuthResponse(access_token=token, user=UserResponse(**user))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, request: Request, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    user, token = await service.login(body.email, body.password, _client_ip(request))
    return AuthResponse(access_token=token, user=UserResponse(**user))


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = AuthService(session)
    user = await service.get_profile(user_id)
    return UserResponse(**user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = AuthService(session)
    photo_url = str(body.profile_photo_url) if body.profile_photo_url else None
    user = await service.update_profile(
        user_id=user_id,
        full_name=body.full_name,
        profile_photo_url=photo_url,
        default_currency=body.default_currency,
    )
    return UserResponse(**user)
