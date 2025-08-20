from abc import ABC, abstractmethod

from app.domain.entities import UserDTO, AutoBuySettingDTO


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, telegram_id: int, username: str) -> UserDTO: ...

    @abstractmethod
    async def get_user_by_telegram_id(
        self, telegram_id: int) -> UserDTO | None: ...

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> UserDTO | None: ...

    @abstractmethod
    async def credit_user_balance(
        self, telegram_id: int, amount: int
    ) -> UserDTO | None: ...

    @abstractmethod
    async def debit_user_balance(
        self, telegram_id: int, amount: int
    ) -> UserDTO | None: ...

    @abstractmethod
    async def get_all_with_auto_buy_enabled(self) -> list[UserDTO]: ...

    @abstractmethod
    async def get_notifications_enabled(self, telegram_id: int) -> bool: ...

    @abstractmethod
    async def set_notifications_enabled(
        self, telegram_id: int, enabled: bool
    ) -> None: ...

    @abstractmethod
    async def get_language(self, telegram_id: int) -> str: ...

    @abstractmethod
    async def set_language(self, telegram_id: int, lang: str) -> None: ...

    @abstractmethod
    async def get_all_with_auto_buy_enabled_and_settings(
        self,
    ) -> list[tuple[UserDTO, AutoBuySettingDTO]]: ...
