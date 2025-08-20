from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.domain.entities import UserDTO, AutoBuySettingDTO
from app.infrastructure.db.models import UserModel
from app.interfaces.repositories import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, telegram_id: int, username: str, language: str = "ru"
    ) -> UserDTO:
        existing_user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        if existing_user:
            return UserDTO(
                id=existing_user.id,
                telegram_id=existing_user.telegram_id,
                username=existing_user.username,
                balance=existing_user.balance,
                role=existing_user.role,
                notifications_enabled=existing_user.notifications_enabled,
                language=existing_user.language,
            )
        db_user = UserModel(
            telegram_id=telegram_id, username=username, language=language
        )
        self.session.add(db_user)
        await self.session.flush()
        return UserDTO(
            id=db_user.id,
            telegram_id=db_user.telegram_id,
            username=db_user.username,
            balance=db_user.balance,
            role=db_user.role,
            notifications_enabled=db_user.notifications_enabled,
            language=db_user.language,
        )

    async def get_user_by_telegram_id(self, telegram_id: int) -> UserDTO | None:
        existing_user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        if not existing_user:
            return None
        return UserDTO(
            id=existing_user.id,
            telegram_id=existing_user.telegram_id,
            username=existing_user.username,
            balance=existing_user.balance,
            role=existing_user.role,
            notifications_enabled=existing_user.notifications_enabled,
            language=existing_user.language,
        )

    async def get_user_by_id(self, user_id: int) -> UserDTO | None:
        existing_user = await self.session.scalar(
            select(UserModel).where(UserModel.id == user_id)
        )
        if not existing_user:
            return None
        return UserDTO(
            id=existing_user.id,
            telegram_id=existing_user.telegram_id,
            username=existing_user.username,
            balance=existing_user.balance,
            role=existing_user.role,
            notifications_enabled=existing_user.notifications_enabled,
            language=existing_user.language,
        )

    async def credit_user_balance(
        self, telegram_id: int, amount: int
    ) -> UserDTO | None:
        existing_user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )

        if not existing_user:
            return None

        existing_user.balance += amount
        return UserDTO(
            id=existing_user.id,
            telegram_id=existing_user.telegram_id,
            username=existing_user.username,
            balance=existing_user.balance,
            role=existing_user.role,
            notifications_enabled=existing_user.notifications_enabled,
            language=existing_user.language,
        )

    async def debit_user_balance(self, telegram_id: int, amount: int) -> UserDTO | None:
        existing_user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )

        if not existing_user:
            return None

        if existing_user.balance < amount:
            return None

        existing_user.balance -= amount
        return UserDTO(
            id=existing_user.id,
            telegram_id=existing_user.telegram_id,
            username=existing_user.username,
            balance=existing_user.balance,
            role=existing_user.role,
            notifications_enabled=existing_user.notifications_enabled,
            language=existing_user.language,
        )

    async def get_all_with_auto_buy_enabled(self) -> list[UserDTO]:
        from app.infrastructure.db.models.auto_buy_setting import AutoBuySettingModel

        result = await self.session.scalars(
            select(UserModel)
            .join(AutoBuySettingModel, UserModel.id == AutoBuySettingModel.user_id)
            .where(AutoBuySettingModel.status)
        )
        users = result.all()
        logger.info(
            f"[UserRepo] Пользователей с автопокупкой (всего): {len(users)}")
        return [
            UserDTO(
                id=u.id,
                telegram_id=u.telegram_id,
                username=u.username,
                balance=u.balance,
                role=u.role,
                notifications_enabled=u.notifications_enabled,
                language=u.language,
            )
            for u in users
        ]

    async def get_all_with_auto_buy_enabled_and_settings(
        self,
    ) -> list[tuple[UserDTO, AutoBuySettingDTO]]:
        from app.infrastructure.db.models.auto_buy_setting import AutoBuySettingModel
        from app.domain.entities.auto_buy_setting import AutoBuySettingDTO

        result = await self.session.execute(
            select(UserModel, AutoBuySettingModel)
            .join(AutoBuySettingModel, UserModel.id == AutoBuySettingModel.user_id)
            .where(AutoBuySettingModel.status)
        )
        rows = result.all()
        users_settings = []
        for user, setting in rows:
            users_settings.append(
                (
                    UserDTO(
                        id=user.id,
                        telegram_id=user.telegram_id,
                        username=user.username,
                        balance=user.balance,
                        role=user.role,
                        notifications_enabled=user.notifications_enabled,
                        language=user.language,
                    ),
                    AutoBuySettingDTO(
                        id=setting.id,
                        user_id=setting.user_id,
                        status=setting.status,
                        price_limit_from=setting.price_limit_from,
                        price_limit_to=setting.price_limit_to,
                        supply_limit=setting.supply_limit,
                        cycles=setting.cycles,
                    ),
                )
            )
        return users_settings

    async def get_notifications_enabled(self, telegram_id: int) -> bool:
        user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        if not user:
            return True
        return user.notifications_enabled

    async def set_notifications_enabled(self, telegram_id: int, enabled: bool) -> None:
        user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        if user:
            user.notifications_enabled = enabled

    async def set_language(self, telegram_id: int, lang: str) -> None:
        user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        if user:
            user.language = lang

    async def get_language(self, telegram_id: int) -> str:
        user = await self.session.scalar(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        return user.language if user else "ru"
