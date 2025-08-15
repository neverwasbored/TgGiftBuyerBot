from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.domain.entities import GiftDTO
from app.infrastructure.db.models import GiftModel
from app.interfaces.repositories import IGiftRepository


class GiftRepository(IGiftRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    @logger.catch
    async def save_all(self, gifts: Sequence[GiftDTO]) -> bool:
        added = 0
        updated_count = 0
        for gift in gifts:
            exists = await self.session.scalar(
                select(GiftModel).where(GiftModel.gift_id == gift.gift_id)
            )
            if not exists:
                self.session.add(
                    GiftModel(
                        gift_id=gift.gift_id,
                        emoji=gift.emoji,
                        star_count=gift.star_count,
                        remaining_count=gift.remaining_count or None,
                        total_count=gift.total_count or None,
                        is_new=True,
                    )
                )
                added += 1
            else:
                updated = False
                if exists.star_count != gift.star_count:
                    exists.star_count = gift.star_count
                    updated = True
                if exists.remaining_count != gift.remaining_count:
                    exists.remaining_count = gift.remaining_count
                    updated = True
                if exists.total_count != gift.total_count:
                    exists.total_count = gift.total_count
                    updated = True
                if updated:
                    exists.is_new = True
                    updated_count += 1
                else:
                    exists.is_new = False
        await self.session.flush()
        logger.info(
            f"[GiftRepo] Добавлено новых подарков: {added}, обновлено: {updated_count}"
        )
        return True

    async def get_new_gifts(self) -> list[GiftDTO]:
        result = await self.session.scalars(select(GiftModel).where(GiftModel.is_new))
        gifts = result.all()
        logger.info(f"[GiftRepo] Найдено новых подарков: {len(gifts)}")
        return [
            GiftDTO(
                id=str(g.id),
                gift_id=g.gift_id,
                emoji=g.emoji,
                star_count=g.star_count,
                remaining_count=g.remaining_count,
                total_count=g.total_count,
                is_new=g.is_new,
            )
            for g in gifts
        ]

    async def reset_new_gifts(self):
        result = await self.session.scalars(select(GiftModel).where(GiftModel.is_new))
        gifts = result.all()
        for g in gifts:
            g.is_new = False
        await self.session.flush()
        logger.info(f"[GiftRepo] Сброшено новых подарков: {len(gifts)}")

    async def reset_new_gift(self, gift_id: int):
        gift = await self.session.scalar(
            select(GiftModel).where(
                GiftModel.gift_id == gift_id, GiftModel.is_new)
        )
        if gift:
            gift.is_new = False
            await self.session.flush()
            logger.info(f"[GiftRepo] Сброшен новый подарок: {gift_id}")
