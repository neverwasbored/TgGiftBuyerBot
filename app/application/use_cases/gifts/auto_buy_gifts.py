import uuid
import time
import asyncio
from typing import TYPE_CHECKING

from aiogram import Bot

from app.core.logger import logger
from app.interfaces.repositories import (
    IAutoBuySettingRepository,
    IGiftRepository,
    IUserRepository,
)
from app.interfaces.services.gifts_service import IGiftsService

from app.interfaces.telegram.messages import MESSAGES

if TYPE_CHECKING:
    from app.application.use_cases.gifts.purchase_gift import PurchaseGift


class AutoBuyGiftsForAllUsers:
    def __init__(
        self,
        user_repo: IUserRepository,
        auto_buy_repo: IAutoBuySettingRepository,
        gift_repo: IGiftRepository,
        gifts_service: IGiftsService,
        purchase_gift_uc: "PurchaseGift",
        transaction_repo,
        bot: Bot,
    ):
        self.user_repo = user_repo
        self.auto_buy_repo = auto_buy_repo
        self.gift_repo = gift_repo
        self.gifts_service = gifts_service
        self.purchase_gift_uc = purchase_gift_uc
        self.transaction_repo = transaction_repo
        self.bot = bot

    async def execute(self):
        logger.info("[UseCase:AutoBuyGifts] Старт автопокупки")
        start_time = time.monotonic()
        users_settings = (
            await self.user_repo.get_all_with_auto_buy_enabled_and_settings()
        )

        if not users_settings:
            logger.info(
                "[UseCase:AutoBuyGifts] Нет пользователей с включенной автопокупкой")
            return

        gifts = await self.gift_repo.get_new_gifts()

        logger.info(
            f"[UseCase:AutoBuyGifts] Пользователей: {len(users_settings)}, новых подарков: {len(gifts)}"
        )

        async def process_user(user, settings):
            suitable = []
            not_suitable = []
            not_enough_balance = []

            for gift in gifts:
                if not (
                    settings.price_limit_from
                    <= gift.star_count
                    <= settings.price_limit_to
                ):
                    not_suitable.append(gift)
                    continue
                if (
                    settings.supply_limit
                    and gift.total_count
                    and gift.total_count > settings.supply_limit
                ):
                    not_suitable.append(gift)
                    continue
                if user.balance < gift.star_count:
                    not_enough_balance.append(gift)
                    continue
                suitable.append(gift)

            lang = getattr(user, "language", "ru")

            msg = f"🎁 Новые подарки! Всего: {len(gifts)}\n"

            if suitable:
                msg += f"{MESSAGES[lang].get('autobuy_suitable', 'Подходят по фильтрам')}: {len(suitable)}\n"
                for gift in suitable:
                    msg += f"• {gift.emoji} ID: {gift.gift_id}, Цена: {gift.star_count}⭐️\n"

            if not_enough_balance:
                msg += f"{MESSAGES[lang].get('autobuy_no_balance', 'Недостаточно баланса')}: {len(not_enough_balance)}\n"
                for gift in not_enough_balance:
                    msg += f"• {gift.emoji} ID: {gift.gift_id}, Цена: {gift.star_count}⭐️\n"

            if not_suitable:
                msg += f"{MESSAGES[lang].get('autobuy_not_suitable', 'Не подходят по фильтрам')}: {len(not_suitable)}\n"
                for gift in not_suitable:
                    msg += f"• {gift.emoji} ID: {gift.gift_id}, Цена: {gift.star_count}⭐️\n"

            if suitable:
                msg += f"\n{MESSAGES[lang].get('autobuy_try_buy', 'Пробую купить подходящие подарки...')}"

            else:
                msg += f"\n{MESSAGES[lang].get('autobuy_no_suitable', 'Нет подходящих подарков для автопокупки.')}"

            try:
                await self.bot.send_message(user.telegram_id, msg)
            except Exception as e:
                logger.error(
                    f"[AutoBuyGifts] Не удалось отправить уведомление {user.telegram_id}: {e}"
                )

            for cycle in range(settings.cycles):
                for gift in suitable:
                    logger.info(
                        f"[AutoBuyGifts] Попытка купить подарок {gift.gift_id} для пользователя {user.telegram_id}, цикл {cycle}, баланс {user.balance}"
                    )
                    payload = (
                        f"autobuy_{gift.gift_id}_to_{user.telegram_id}_cycle{cycle}"
                    )
                    provider_charge_id = f"{payload}_{uuid.uuid4().hex}"
                    result = await self.purchase_gift_uc.execute(
                        buyer_telegram_id=user.telegram_id,
                        recipient_id=user.telegram_id,
                        gift_id=gift.gift_id,
                        gifts_count=1,
                        payload=payload,
                        provider_charge_id=provider_charge_id,
                    )
                    if result["ok"]:
                        user = result["user"]
                        try:
                            await self.bot.send_message(
                                user.telegram_id,
                                f"✅ Куплен подарок {gift.emoji} (ID: {gift.gift_id}) за {gift.star_count}⭐️. Остаток: {result['user'].balance}⭐️.",
                            )
                        except Exception as e:
                            logger.error(
                                f"[AutoBuyGifts] Не удалось отправить подтверждение покупки {user.telegram_id}: {e}"
                            )
                    elif result.get("error_code") == "STARGIFT_USAGE_LIMITED":
                        try:
                            await self.bot.send_message(
                                user.telegram_id,
                                f"❌ Подарок {gift.emoji} (ID: {gift.gift_id}) временно недоступен для покупки (лимит использования). Будет предпринята попытка позже.",
                            )
                        except Exception as e:
                            logger.error(
                                f"[AutoBuyGifts] Не удалось отправить ошибку лимита {user.telegram_id}: {e}"
                            )
                        break
                    else:
                        try:
                            await self.bot.send_message(
                                user.telegram_id,
                                f"❌ Не удалось купить подарок {gift.emoji} (ID: {gift.gift_id}): {result['error']}",
                            )
                        except Exception as e:
                            logger.error(
                                f"[AutoBuyGifts] Не удалось отправить ошибку покупки {user.telegram_id}: {e}"
                            )

        await asyncio.gather(
            *(process_user(user, settings) for user, settings in users_settings)
        )
        await self.gift_repo.reset_new_gifts()
        elapsed = time.monotonic() - start_time
        logger.info(f"[UseCase:AutoBuyGifts] Завершено за {elapsed:.2f} сек")
