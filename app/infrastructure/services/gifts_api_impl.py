import aiohttp

from app.core.config import settings
from app.core.logger import logger
from app.domain.entities import GiftDTO


class TelegramGiftsApi:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._base_url = f"https://api.telegram.org/bot{settings.bot_token}"

    @logger.catch
    async def get_available_gifts(self) -> list[GiftDTO] | None:
        url = f"{self._base_url}/getAvailableGifts"
        try:
            async with self._session.get(url) as resp:
                data = await resp.json()

            if not data.get("ok"):
                logger.error(f"[GiftsApi] Телеграм вернул ошибку: {data}")
                return None

            gifts = data["result"]["gifts"]
            logger.info(f"[GiftsApi] Получены подарки: {gifts}")
            logger.info(f"[GiftsApi] Получено подарков: {len(gifts)}")
            return [
                GiftDTO(
                    id=gift["id"],
                    gift_id=int(gift["id"]),
                    emoji=gift["sticker"]["emoji"],
                    star_count=gift["star_count"],
                    remaining_count=gift.get("remaining_count", None),
                    total_count=gift.get("total_count", None),
                )
                for gift in gifts
            ]
        except Exception as e:
            logger.error(f"[GiftsApi] Ошибка getAvailableGifts: {e}")
            return None

    @logger.catch
    async def send_gift(
        self, user_id: int, gift_id: str, pay_for_upgrade: bool = False
    ) -> bool:
        url = f"{self._base_url}/sendGift"
        payload = {
            "user_id": user_id,
            "gift_id": gift_id,
            "pay_for_upgrade": pay_for_upgrade,
        }

        try:
            async with self._session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    logger.info(
                        f"[GiftsApi] Подарок {gift_id} успешно отправлен пользователю {user_id}"
                    )
                    return True
                else:
                    logger.error(
                        f"[GiftsApi] Ошибка отправки подарка: {data.get('description')}"
                    )
                    return False
        except Exception as e:
            logger.error(f"[GiftsApi] Ошибка при отправке подарка: {e}")
            return False

    @logger.catch
    async def refund_payment(
        self, telegram_payment_charge_id: str, user_id: int
    ) -> bool:
        url = f"{self._base_url}/refundStarPayment"
        payload = {
            "telegram_payment_charge_id": telegram_payment_charge_id,
            "user_id": user_id,
        }

        try:
            async with self._session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    logger.info(
                        f"[GiftsApi] Платеж {telegram_payment_charge_id} успешно возвращен"
                    )
                    return True
                else:
                    logger.error(
                        f"[GiftsApi] Ошибка возврата платежа: {data.get('description')}"
                    )
                    return False
        except Exception as e:
            logger.error(f"[GiftsApi] Ошибка при возврате платежа: {e}")
            return False
