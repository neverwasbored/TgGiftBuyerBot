from datetime import datetime

import aiohttp
from aiogram import types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from api.gifts import GiftsApi
from utils.logger import log
from bot.states.gift_state import GiftStates
from bot.keyboards.inline import payment_keyboard
from bot.keyboards.default import go_back_menu, main_menu
from db.models import User, Transaction

router = Router()
gifts_api = GiftsApi()


@log.catch
async def return_to_main_menu(message: types.Message, state: FSMContext) -> None:
    """
    Return user to main menu and clear current state.
    """
    await state.clear()
    await message.answer(
        text='You have returned to the main menu! Please use the buttons below to continue.',
        reply_markup=main_menu()
    )


@log.catch
async def fetch_gifts_list(limited_only: bool = False) -> list | None:
    """
    Fetch available gifts list from API.
    
    Args:
        limited_only: If True, return only limited gifts (with total_count)
    
    Returns:
        list: List of available gifts (filtered if requested)
        None: If error occurs
    """
    try:
        async with aiohttp.ClientSession() as session:
            gifts = await gifts_api.aio_get_available_gifts(session=session)
            
            if gifts and limited_only:
                # Фильтруем только лимитированные подарки
                limited_gifts = [
                    gift for gift in gifts 
                    if gift.get('total_count') is not None and gift.get('remaining_count') is not None
                ]
                log.info(f"Filtered gifts: {len(limited_gifts)} limited out of {len(gifts)} total")
                return limited_gifts
            
            return gifts
    except Exception as e:
        log.error(f"Error fetching gifts list: {e}")
        return None


@log.catch
async def process_gift_payment(
    message: types.Message,
    db_session,
    payment_info: types.SuccessfulPayment = None,
    from_balance: bool = False
) -> None:
    """
    Process gift payment and send gifts to recipient.
    """
    if not from_balance:
        payload = payment_info.invoice_payload
        parts = payload.split("_")
        gift_id = parts[1]
        user_id = parts[3]
        gifts_count = int(parts[5])
    else:
        parts = message.text.split()
        gift_id = parts[0]
        user_id = parts[1]
        gifts_count = int(parts[2])
        payload = f"gift_{gift_id}_to_{user_id}_count_{gifts_count}"

    # Получаем ВСЕ подарки для проверки цены (включая unlimited)
    gifts_list = await fetch_gifts_list(limited_only=False)
    gift_price = None
    for gift in gifts_list:
        if str(gift_id) == str(gift.get('id')):
            gift_price = gift.get('star_count')
            break

    if gift_price is None:
        raise ValueError("Invalid gift ID or price retrieval error.")

    amount = int(gift_price) * gifts_count
    telegram_payment_charge_id = 'buy_gift_transaction' if from_balance else payment_info.telegram_payment_charge_id

    try:
        with db_session as db:
            user = db.query(User).filter(
                User.user_id == message.from_user.id).first()
            if not user:
                raise ValueError("User not found in database.")

            for _ in range(gifts_count):
                result = await gifts_api.send_gift(user_id=user_id, gift_id=gift_id)
                if result:
                    log.info(f"Gift {gift_id} successfully sent to user {user_id}.")
                else:
                    log.warning(f"Error sending gift {gift_id} to user {user_id}.")
                    await message.reply(f"Error sending gift to user {user_id}. Stars were preserved.")

            transaction = Transaction(
                user_id=message.from_user.id,
                amount=amount,
                telegram_payment_charge_id=telegram_payment_charge_id,
                status="completed",
                time=datetime.now().isoformat(),
                payload=payload
            )
            db.add(transaction)
            db.commit()

        await message.reply(f"Gift with ID {gift_id} successfully sent to user {user_id}.")
    except Exception as e:
        log.error(f"Error processing gifts: {e}")
        await message.reply("An error occurred while processing gifts. Please try again later.")


@log.catch
@router.message(Command(commands=["buy_gift"]))
async def buy_gift_command(message: types.Message, state: FSMContext) -> None:
    """
    Initiate gift purchase process.
    Shows only LIMITED gifts (not unlimited).
    """
    # Получаем только лимитированные подарки
    gifts_list = await fetch_gifts_list(limited_only=True)
    
    if not gifts_list:
        await message.reply(
            "Currently no limited gifts available. Only unlimited gifts are in stock.\n"
            "Limited gifts have specific quantities and are more exclusive! 🎁"
        )
        return

    # Сортируем по ID
    sorted_gifts = sorted(gifts_list, key=lambda gift: int(gift.get("id", 0)), reverse=False)
    
    # Форматируем описания только для лимитированных подарков
    gift_descriptions = [
        f'Gift: {gift.get("sticker", {}).get("emoji", "🎁")}\n'
        f'ID: <code>{gift["id"]}</code>\n'
        f'Price: {gift["star_count"]}⭐️\n'
        f'Available: {gift.get("remaining_count", 0)}/{gift.get("total_count", 0)}\n'
        for gift in sorted_gifts
    ]

    # Добавляем заголовок
    header = (
        "🎁 <b>LIMITED GIFTS ONLY</b> 🎁\n"
        f"Found {len(gift_descriptions)} limited gifts:\n\n"
    )
    
    await message.answer(header + "\n".join(gift_descriptions), parse_mode="HTML")
    
    # Добавляем инструкцию
    await message.answer(
        text=(
            "Enter gift ID, recipient ID and quantity.\n"
            "Example: 12345678 87654321 10\n\n"
            "💡 Note: Only limited gifts are shown above."
        ),
        reply_markup=go_back_menu()
    )
    await state.set_state(GiftStates.waiting_for_gift_id)


@log.catch
@router.message(Command(commands=["buy_gift_all"]))
async def buy_gift_all_command(message: types.Message, state: FSMContext) -> None:
    """
    Show ALL gifts including unlimited ones.
    """
    gifts_list = await fetch_gifts_list(limited_only=False)
    
    if not gifts_list:
        await message.reply("Currently no gifts available.")
        return

    sorted_gifts = sorted(gifts_list, key=lambda gift: int(gift.get("id", 0)), reverse=False)
    
    # Разделяем на лимитированные и unlimited
    limited_gifts = [g for g in sorted_gifts if g.get('total_count') is not None]
    unlimited_gifts = [g for g in sorted_gifts if g.get('total_count') is None]
    
    # Форматируем вывод
    response = f"🎁 <b>ALL GIFTS</b> 🎁\n\n"
    
    if limited_gifts:
        response += f"<b>LIMITED GIFTS ({len(limited_gifts)}):</b>\n"
        for gift in limited_gifts[:10]:  # Показываем первые 10
            response += (
                f'• {gift.get("sticker", {}).get("emoji", "🎁")} '
                f'ID: <code>{gift["id"]}</code> | '
                f'{gift["star_count"]}⭐️ | '
                f'{gift.get("remaining_count", 0)}/{gift.get("total_count", 0)}\n'
            )
        if len(limited_gifts) > 10:
            response += f"... and {len(limited_gifts) - 10} more\n"
    
    if unlimited_gifts:
        response += f"\n<b>UNLIMITED GIFTS ({len(unlimited_gifts)}):</b>\n"
        for gift in unlimited_gifts[:10]:  # Показываем первые 10
            response += (
                f'• {gift.get("sticker", {}).get("emoji", "🎁")} '
                f'ID: <code>{gift["id"]}</code> | '
                f'{gift["star_count"]}⭐️\n'
            )
        if len(unlimited_gifts) > 10:
            response += f"... and {len(unlimited_gifts) - 10} more\n"
    
    await message.answer(response, parse_mode="HTML")
    
    await message.answer(
        text="Enter gift ID, recipient ID and quantity.\nExample: 12345678 87654321 10",
        reply_markup=go_back_menu()
    )
    await state.set_state(GiftStates.waiting_for_gift_id)


@log.catch
@router.message(StateFilter(GiftStates.waiting_for_gift_id))
async def process_gift_id_input(
    message: types.Message,
    state: FSMContext,
    db_session
) -> None:
    """
    Process gift purchase details and handle payment.
    """
    if message.text == "/go_back":
        await return_to_main_menu(message, state)
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.reply("Enter gift ID, recipient ID and quantity separated by spaces.")
            return

        try:
            gift_id, user_id, gifts_count = map(int, parts)
        except ValueError:
            await message.reply("All values must be numbers.")
            return

        payload = f"gift_{gift_id}_to_{user_id}_count_{gifts_count}"

        # Получаем ВСЕ подарки для проверки (включая unlimited)
        gifts_list = await fetch_gifts_list(limited_only=False)
        gift_price = next(
            (gift["star_count"] for gift in gifts_list if int(gift["id"]) == gift_id), None)
        if gift_price is None:
            await message.reply("Gift with specified ID not found.")
            return

        amount = gift_price * gifts_count

        with db_session as db:
            user = db.query(User).filter(
                User.user_id == message.from_user.id).first()
            if not user:
                await message.reply("User not found.")
                return

            if user.balance >= amount:
                user.balance -= amount

                transaction = Transaction(
                    user_id=user.user_id,
                    amount=amount,
                    telegram_payment_charge_id="local_transaction",
                    status="completed",
                    time=datetime.now().isoformat(),
                    payload=payload
                )
                db.add(transaction)
                db.commit()

                await message.reply(f"Purchase successful! Remaining balance: {user.balance}⭐️.")
                await process_gift_payment(message=message, db_session=db_session, from_balance=True)
            else:
                required_amount = amount - user.balance
                prices = [types.LabeledPrice(
                    label="Additional deposit", amount=required_amount)]
                await message.answer_invoice(
                    title="Additional deposit",
                    description=f"Purchase requires {amount}⭐️, you have {user.balance}⭐️.",
                    payload=payload,
                    currency="XTR",
                    prices=prices,
                    provider_token="",
                    reply_markup=payment_keyboard(price=required_amount)
                )
                await state.clear()

    except Exception as e:
        log.error(f"Error: {e}")
        await message.reply("An error occurred. Please try again.")