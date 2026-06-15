import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.logging import log_event
from app.core.security import create_access_token, hash_password, verify_password
from app.integrations.redis_client import get_redis
from app.repositories import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.settings = get_settings()

    async def register(self, email: str, password: str, full_name: str, default_currency: str) -> tuple[dict, str]:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        currency = default_currency.upper()
        if currency not in self.settings.supported_currencies:
            raise ValidationError(f"Unsupported currency: {default_currency}")

        existing = await self.users.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered")

        user = await self.users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            default_currency=currency,
        )
        await self.session.commit()

        token = create_access_token(str(user.id))
        log_event(logger, "auth.register", user_id=str(user.id), email=user.email)
        return self._user_response(user), token

    async def login(self, email: str, password: str, client_ip: str) -> tuple[dict, str]:
        await self._check_rate_limit(email, client_ip)

        result = await self.users.get_by_email(email)
        if not result:
            await self._record_failed_login(email, client_ip)
            raise AuthenticationError("Invalid email or password")

        user, password_hash = result
        if not verify_password(password, password_hash):
            await self._record_failed_login(email, client_ip)
            log_event(logger, "auth.failed", level=logging.WARNING, email=email, ip=client_ip)
            raise AuthenticationError("Invalid email or password")

        await self._clear_rate_limit(email, client_ip)
        token = create_access_token(str(user.id))
        log_event(logger, "auth.login", user_id=str(user.id), email=user.email)
        return self._user_response(user), token

    async def get_profile(self, user_id: UUID) -> dict:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        return self._user_response(user)

    async def update_profile(
        self,
        user_id: UUID,
        full_name: str | None = None,
        profile_photo_url: str | None = None,
        default_currency: str | None = None,
    ) -> dict:
        if default_currency and default_currency.upper() not in self.settings.supported_currencies:
            raise ValidationError(f"Unsupported currency: {default_currency}")

        user = await self.users.update_profile(
            user_id=user_id,
            full_name=full_name,
            profile_photo_url=profile_photo_url,
            default_currency=default_currency.upper() if default_currency else None,
        )
        if not user:
            raise NotFoundError("User", str(user_id))
        await self.session.commit()
        log_event(logger, "auth.profile_updated", user_id=str(user_id))
        return self._user_response(user)

    async def _check_rate_limit(self, email: str, client_ip: str) -> None:
        from app.core.exceptions import RateLimitError

        redis = await get_redis()
        key = f"login_attempts:{email.lower()}:{client_ip}"
        attempts = await redis.get(key)
        if attempts and int(attempts) >= self.settings.login_rate_limit_attempts:
            raise RateLimitError("Too many login attempts. Try again later.")

    async def _record_failed_login(self, email: str, client_ip: str) -> None:
        redis = await get_redis()
        key = f"login_attempts:{email.lower()}:{client_ip}"
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.settings.login_rate_limit_window_seconds)
        await pipe.execute()

    async def _clear_rate_limit(self, email: str, client_ip: str) -> None:
        redis = await get_redis()
        key = f"login_attempts:{email.lower()}:{client_ip}"
        await redis.delete(key)

    @staticmethod
    def _user_response(user) -> dict:
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "profile_photo_url": user.profile_photo_url,
            "default_currency": user.default_currency,
            "created_at": user.created_at.isoformat(),
        }
