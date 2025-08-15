from app.core.logger import logger
from app.domain.entities import GiftDTO, UserDTO
from app.infrastructure.db.enums import TransactionStatus
from app.interfaces.repositories import ITransactionRepository, IUserRepository
from app.interfaces.services.gifts_service import IGiftsService


class PurchaseGift:
    def __init__(
        self,
        user_repo: IUserRepository,
        transaction_repo: ITransactionRepository,
        gifts_service: IGiftsService,
    ):
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo
        self.gifts_service = gifts_service

    async def execute(
        self,
        buyer_telegram_id: int,
        recipient_id: int,
        gift_id: int,
        gifts_count: int,
        payload: str,
        provider_charge_id: str = None,
    ) -> dict:
        if provider_charge_id is None:
            provider_charge_id = payload
        logger.info(
            f"[UseCase:PurchaseGift] Старт: buyer={buyer_telegram_id}, recipient={recipient_id}, gift={gift_id}, count={gifts_count}"
        )

        if str(recipient_id).startswith("-100"):
            logger.error("[UseCase:PurchaseGift] Ошибка: recipient_is_channel")
            return {"ok": False, "error": "recipient_is_channel"}

        user: UserDTO = await self.user_repo.get_user_by_telegram_id(buyer_telegram_id)
        if not user:
            logger.error("[UseCase:PurchaseGift] Ошибка: user_not_found")
            return {"ok": False, "error": "user_not_found"}

        logger.info(f"[UseCase:PurchaseGift] Баланс до: {user.balance}")
        gifts: list[GiftDTO] = await self.gifts_service.get_available_gifts()
        gift = next((g for g in gifts if int(g.gift_id) == int(gift_id)), None)
        if not gift:
            logger.error("[UseCase:PurchaseGift] Ошибка: gift_not_found")
            return {"ok": False, "error": "gift_not_found"}
        logger.info(
            f"[UseCase:PurchaseGift] Параметры подарка: id={gift.gift_id}, price={gift.star_count}, total={gift.total_count}"
        )

        amount = gift.star_count * gifts_count
        if user.balance < amount:
            logger.error("[UseCase:PurchaseGift] Ошибка: not_enough_balance")
            return {
                "ok": False,
                "error": "not_enough_balance",
                "required": amount - user.balance,
                "gift_price": gift.star_count,
            }

        for _ in range(gifts_count):
            sent = await self.gifts_service.send_gift(
                user_id=recipient_id, gift_id=gift_id
            )
            if not sent:
                error_code = None
                if (
                    isinstance(sent, dict)
                    and sent.get("error_code") == "STARGIFT_USAGE_LIMITED"
                ):
                    error_code = "STARGIFT_USAGE_LIMITED"
                logger.error("[UseCase:PurchaseGift] Ошибка: gift_send_failed")
                return {
                    "ok": False,
                    "error": "gift_send_failed",
                    "error_code": error_code,
                }

        user = await self.user_repo.debit_user_balance(buyer_telegram_id, amount)
        if not user:
            logger.error("[UseCase:PurchaseGift] Ошибка: debit_failed")
            return {"ok": False, "error": "debit_failed"}
        logger.info(f"[UseCase:PurchaseGift] Баланс после: {user.balance}")

        transaction = await self.transaction_repo.create(
            user_id=user.id,
            amount=amount,
            telegram_payment_charge_id=provider_charge_id,
            status=TransactionStatus.COMPLETED,
            payload=payload,
        )
        if not transaction:
            logger.error("[UseCase:PurchaseGift] Ошибка: transaction_failed")
            return {"ok": False, "error": "transaction_failed"}
        logger.info(
            f"[UseCase:PurchaseGift] Транзакция: id={transaction.id}, amount={amount}, status={transaction.status}"
        )

        logger.info(
            f"[UseCase:PurchaseGift] Успех: buyer={buyer_telegram_id}, recipient={recipient_id}, gift={gift_id}, count={gifts_count}"
        )
        return {
            "ok": True,
            "user": user,
            "transaction": transaction,
            "gift": gift,
            "amount": amount,
        }
