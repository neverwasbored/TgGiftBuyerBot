import asyncio
import aiohttp
from datetime import datetime

from utils.logger import log
from api.gifts import GiftsApi
from db.models import Gift, AutoBuySettings, User, Transaction
from db.session import get_db_session


async def process_gift_purchase(db, gifts_api, user, settings, gift):
    """
    Process the purchase of a single gift for a user.
    SKIPS unlimited gifts automatically.
    """
    gift_price = gift.price
    total_count = gift.total_count
    remaining_count = gift.remaining_count
    price_limit_from = settings.price_limit_from
    price_limit_to = settings.price_limit_to
    supply_limit = settings.supply_limit

    # ВАЖНО: Пропускаем unlimited подарки
    if total_count is None or remaining_count is None:
        log.debug(
            f"Skipping unlimited gift {gift.gift_id} for user {user.user_id} "
            f"(total_count={total_count}, remaining_count={remaining_count})"
        )
        return False

    # Дополнительная проверка на 0 remaining_count
    if remaining_count == 0:
        log.debug(f"Skipping sold out gift {gift.gift_id} (remaining_count=0)")
        return False

    if (
        gift_price is not None and
        price_limit_from <= gift_price <= price_limit_to and
        (supply_limit is None or total_count <= supply_limit) and
        user.balance >= gift_price
    ):
        success = await gifts_api.send_gift(
            user_id=user.user_id,
            gift_id=gift.gift_id,
            pay_for_upgrade=False
        )
        if success:
            log.info(
                f"✅ Gift {gift.gift_id} successfully sent to user {user.user_id}. "
                f"Price: {gift_price}⭐, Remaining: {remaining_count-1}/{total_count}"
            )
            user.balance -= gift_price
            new_transaction = Transaction(
                user_id=user.user_id,
                amount=-gift_price,
                telegram_payment_charge_id="buy_gift_transaction",
                payload=f"Autobuy_of_gift_{gift.gift_id}",
                status="completed",
                time=datetime.utcnow().isoformat(),
            )
            db.add(new_transaction)
            return True
        else:
            log.warning(
                f"❌ Failed to send gift {gift.gift_id} to user {user.user_id}."
            )
    else:
        log.debug(
            f"Conditions not met for gift {gift.gift_id} for user {user.user_id}: "
            f"Price: {gift_price} (limits: {price_limit_from}-{price_limit_to}), "
            f"Total: {total_count} (limit: {supply_limit}), "
            f"Balance: {user.balance}"
        )
    return False

# Часть для start_gift_parsing_loop в utils/gift_parser.py

async def start_gift_parsing_loop():
    """
    Continuously parse new gifts and automatically process purchases for eligible users.
    FILTERS OUT unlimited gifts.
    """
    gifts_api = GiftsApi()
    session_timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=session_timeout) as session:
        while True:
            try:
                # Retrieve the list of available gifts via API
                gifts = await gifts_api.aio_get_available_gifts(session)
                if not gifts:
                    log.warning("Gift list is empty or an error occurred while retrieving data.")
                    await asyncio.sleep(10)
                    continue

                # Статистика по подаркам
                total_gifts = len(gifts)
                unlimited_gifts = [g for g in gifts if g.get('total_count') is None or g.get('remaining_count') is None]
                limited_gifts = [g for g in gifts if g.get('total_count') is not None and g.get('remaining_count') is not None]
                
                log.info(
                    f"📊 Gifts fetched - Total: {total_gifts}, "
                    f"Limited: {len(limited_gifts)}, "
                    f"Unlimited: {len(unlimited_gifts)} (will be ignored)"
                )

                with get_db_session() as db:
                    # Update or create gift records in the database
                    # Обрабатываем ТОЛЬКО лимитированные подарки
                    for gift in gifts:
                        # Пропускаем unlimited подарки
                        if gift.get('total_count') is None or gift.get('remaining_count') is None:
                            continue
                            
                        existing_gift = db.query(Gift).filter(
                            Gift.gift_id == gift['id']).first()
                            
                        if existing_gift:
                            updated = False
                            if existing_gift.price != gift.get('star_count', 0):
                                existing_gift.price = gift.get('star_count', 0)
                                updated = True
                            if existing_gift.remaining_count != gift.get('remaining_count'):
                                existing_gift.remaining_count = gift.get('remaining_count')
                                updated = True
                            if existing_gift.total_count != gift.get('total_count'):
                                existing_gift.total_count = gift.get('total_count')
                                updated = True

                            if updated:
                                log.info(
                                    f"📝 Updated gift {existing_gift.gift_id}: "
                                    f"price={existing_gift.price}⭐, "
                                    f"remaining={existing_gift.remaining_count}/{existing_gift.total_count}"
                                )
                        else:
                            new_gift = Gift(
                                gift_id=gift['id'],
                                price=gift.get('star_count', 0),
                                remaining_count=gift.get('remaining_count'),
                                total_count=gift.get('total_count'),
                                is_new=True
                            )
                            db.add(new_gift)
                            log.info(
                                f"🆕 Added new LIMITED gift: {new_gift.gift_id} "
                                f"({new_gift.price}⭐, {new_gift.remaining_count}/{new_gift.total_count})"
                            )

                    db.commit()
                    log.info("✅ Database updated with LIMITED gifts only")

                    # Retrieve users with auto-purchase enabled
                    auto_buy_users = db.query(AutoBuySettings).filter(
                        AutoBuySettings.status == "enabled"
                    ).all()
                    
                    if auto_buy_users:
                        log.info(f"👥 Found {len(auto_buy_users)} users with autobuy enabled")
                    
                    # Retrieve the list of newly added gifts for processing
                    new_gifts = db.query(Gift).filter(Gift.is_new == 1).all()
                    
                    if new_gifts:
                        log.info(f"🎁 Processing {len(new_gifts)} new gifts for autobuy")

                    for settings in auto_buy_users:
                        user = db.query(User).filter(
                            User.user_id == settings.user_id).first()
                        if not user:
                            continue

                        purchased_count = 0
                        for cycle in range(settings.cycles):
                            log.debug(f"Cycle {cycle + 1}/{settings.cycles} for user {user.user_id}")
                            
                            for gift in new_gifts:
                                if user.balance < gift.price:
                                    log.debug(
                                        f"Insufficient funds for user {user.user_id} "
                                        f"(balance: {user.balance}⭐, gift price: {gift.price}⭐)"
                                    )
                                    continue

                                purchase_success = await process_gift_purchase(db, gifts_api, user, settings, gift)
                                if purchase_success:
                                    purchased_count += 1
                                    db.commit()  # Commit changes after a successful purchase
                        
                        if purchased_count > 0:
                            log.info(f"🛒 User {user.user_id} purchased {purchased_count} gifts")

                    # Reset the 'is_new' flag after processing new gifts
                    for gift in new_gifts:
                        gift.is_new = 0
                    db.commit()

                await asyncio.sleep(3)
            except Exception as e:
                log.error(f"❌ Error in gift parsing process: {e}")
                await asyncio.sleep(3)
