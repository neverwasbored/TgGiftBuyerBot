import json
import aiohttp
from aiogram import types, Router
from aiogram.filters import Command

from api.gifts import GiftsApi
from utils.logger import log

router = Router()
gifts_api = GiftsApi()


@router.message(Command(commands=["gift_stats"]))
async def gift_statistics(message: types.Message, db_session):
    """
    Show statistics about gifts in the system.
    """
    try:
        # Получаем свежие данные с API
        async with aiohttp.ClientSession() as session:
            api_gifts = await gifts_api.aio_get_available_gifts(session)
        
        if not api_gifts:
            await message.answer("❌ Failed to fetch gifts from API")
            return
        
        # Анализируем подарки
        total_api = len(api_gifts)
        unlimited_api = len([g for g in api_gifts if g.get('total_count') is None or g.get('remaining_count') is None])
        limited_api = total_api - unlimited_api
        
        # Получаем данные из БД
        with db_session as db:
            from db.models import Gift
            
            db_gifts = db.query(Gift).all()
            new_db_gifts = db.query(Gift).filter(Gift.is_new == 1).all()
            
            # Статистика по ценам в БД
            if db_gifts:
                prices = [g.price for g in db_gifts if g.price]
                min_price = min(prices) if prices else 0
                max_price = max(prices) if prices else 0
                avg_price = sum(prices) / len(prices) if prices else 0
            else:
                min_price = max_price = avg_price = 0
        
        stats_text = (
            "📊 **GIFT STATISTICS**\n\n"
            "**API Data:**\n"
            f"• Total gifts from API: {total_api}\n"
            f"• Limited gifts: {limited_api} ✅\n"
            f"• Unlimited gifts: {unlimited_api} ❌ (ignored)\n\n"
            "**Database Data:**\n"
            f"• Gifts in DB: {len(db_gifts)} (only limited)\n"
            f"• New gifts for autobuy: {len(new_db_gifts)}\n\n"
        )
        
        if db_gifts:
            stats_text += (
                "**Price Range (DB):**\n"
                f"• Min: {min_price}⭐\n"
                f"• Max: {max_price}⭐\n"
                f"• Average: {avg_price:.1f}⭐\n\n"
            )
        
        # Примеры лимитированных подарков
        limited_examples = [g for g in api_gifts if g.get('total_count') is not None][:5]
        if limited_examples:
            stats_text += "**Limited Gift Examples:**\n"
            for gift in limited_examples:
                stats_text += (
                    f"• {gift.get('sticker', {}).get('emoji', '🎁')} "
                    f"ID: {gift['id']} | {gift['star_count']}⭐ | "
                    f"{gift.get('remaining_count')}/{gift.get('total_count')}\n"
                )
        
        await message.answer(stats_text, parse_mode="Markdown")
        
    except Exception as e:
        log.error(f"Error in gift_statistics: {e}")
        await message.answer(f"❌ Error: {str(e)}")


@router.message(Command(commands=["raw_api"]))
async def raw_api_response(message: types.Message):
    """
    Show raw API response structure without any filtering.
    """
    try:
        url = f"https://api.telegram.org/bot{gifts_api.bot_token}/getAvailableGifts"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                
                # Показываем структуру ответа
                structure_info = (
                    "🔍 **Raw API Response Structure:**\n\n"
                    f"• Status: {'✅ OK' if data.get('ok') else '❌ Error'}\n"
                    f"• Top-level keys: {list(data.keys())}\n"
                )
                
                if data.get('ok') and 'result' in data:
                    result = data['result']
                    structure_info += f"• Result keys: {list(result.keys())}\n"
                    
                    if 'gifts' in result:
                        gifts = result['gifts']
                        structure_info += f"• Total gifts in response: {len(gifts)}\n"
                        
                        if gifts:
                            first_gift = gifts[0]
                            structure_info += f"\n**First gift structure:**\n"
                            structure_info += f"• Keys: {list(first_gift.keys())}\n"
                            
                            # Показываем типы данных
                            for key, value in first_gift.items():
                                value_type = type(value).__name__
                                if isinstance(value, dict):
                                    structure_info += f"• {key}: {value_type} with keys {list(value.keys())}\n"
                                else:
                                    structure_info += f"• {key}: {value_type}\n"
                
                await message.answer(structure_info, parse_mode="Markdown")
                
                # Отправляем сырой JSON первого подарка
                if data.get('ok') and data.get('result', {}).get('gifts'):
                    first_gift_json = json.dumps(
                        data['result']['gifts'][0], 
                        indent=2, 
                        ensure_ascii=False
                    )
                    await message.answer(
                        f"```json\n{first_gift_json}\n```",
                        parse_mode="Markdown"
                    )
                
    except Exception as e:
        log.error(f"Error in raw_api_response: {e}")
        await message.answer(f"❌ Error: {str(e)}")


@router.message(Command(commands=["debug_gifts"]))
async def debug_gifts_command(message: types.Message):
    """
    Debug command to see raw JSON response from gifts API.
    """
    try:
        await message.answer("🔍 Fetching gifts data...")
        
        async with aiohttp.ClientSession() as session:
            gifts = await gifts_api.aio_get_available_gifts(session)
            
            if gifts:
                # Подготавливаем краткую информацию
                summary = f"📊 Total gifts found: {len(gifts)}\n\n"
                
                for idx, gift in enumerate(gifts[:10]):  # Показываем первые 10
                    summary += (
                        f"Gift #{idx + 1}:\n"
                        f"• ID: {gift.get('id')}\n"
                        f"• Price: {gift.get('star_count')}⭐\n"
                        f"• Remaining: {gift.get('remaining_count', 'Unlimited')}\n"
                        f"• Total: {gift.get('total_count', 'Unlimited')}\n"
                        f"• Emoji: {gift.get('sticker', {}).get('emoji', 'N/A')}\n\n"
                    )
                
                if len(gifts) > 10:
                    summary += f"... and {len(gifts) - 10} more gifts\n"
                
                await message.answer(summary)
                
                # Отправляем полный JSON файл
                json_content = json.dumps({"gifts": gifts}, indent=2, ensure_ascii=False)
                json_file = types.BufferedInputFile(
                    json_content.encode('utf-8'), 
                    filename="gifts_full_response.json"
                )
                
                await message.answer_document(
                    document=json_file,
                    caption="📎 Full JSON response with all gifts data"
                )
                
                # Дополнительно отправляем только лимитированные подарки
                limited_gifts = [g for g in gifts if g.get('total_count') is not None]
                if limited_gifts:
                    limited_json = json.dumps(
                        {"limited_gifts": limited_gifts}, 
                        indent=2, 
                        ensure_ascii=False
                    )
                    limited_file = types.BufferedInputFile(
                        limited_json.encode('utf-8'),
                        filename="limited_gifts_only.json"
                    )
                    await message.answer_document(
                        document=limited_file,
                        caption=f"🎁 Limited gifts only ({len(limited_gifts)} items)"
                    )
                
            else:
                await message.answer("❌ Failed to fetch gifts data. Check logs for details.")
                
    except Exception as e:
        log.error(f"Error in debug_gifts command: {e}")
        await message.answer(f"❌ Error: {str(e)}")


@router.message(Command(commands=["check_autobuy"]))
async def check_autobuy_status(message: types.Message, db_session):
    """
    Check detailed autobuy status and conditions.
    """
    try:
        with db_session as db:
            from db.models import User, AutoBuySettings, Gift
            
            user = db.query(User).filter(User.user_id == message.from_user.id).first()
            if not user:
                await message.answer("❌ User not found")
                return
                
            settings = db.query(AutoBuySettings).filter(
                AutoBuySettings.user_id == message.from_user.id
            ).first()
            
            if not settings:
                await message.answer("❌ Autobuy settings not found")
                return
            
            # Получаем новые подарки
            new_gifts = db.query(Gift).filter(Gift.is_new == 1).all()
            
            status_text = (
                f"🔍 **Autobuy Debug Info**\n\n"
                f"Status: {'🟢 Enabled' if settings.status == 'enabled' else '🔴 Disabled'}\n"
                f"Your balance: {user.balance}⭐\n"
                f"Price range: {settings.price_limit_from} - {settings.price_limit_to}⭐\n"
                f"Supply limit: {settings.supply_limit or 'Not set'}\n"
                f"Cycles: {settings.cycles}\n\n"
                f"📦 New gifts in DB: {len(new_gifts)}\n"
            )
            
            if new_gifts:
                status_text += "\n**New gifts available for autobuy:**\n"
                for gift in new_gifts[:5]:
                    can_buy = (
                        gift.price is not None and
                        settings.price_limit_from <= gift.price <= settings.price_limit_to and
                        (settings.supply_limit is None or 
                         (gift.total_count is not None and gift.total_count <= settings.supply_limit)) and
                        user.balance >= gift.price
                    )
                    
                    status_text += (
                        f"\n• Gift {gift.gift_id}:\n"
                        f"  Price: {gift.price}⭐\n"
                        f"  Total: {gift.total_count or 'Unlimited'}\n"
                        f"  Can buy: {'✅ Yes' if can_buy else '❌ No'}\n"
                    )
                    
                    if not can_buy:
                        reasons = []
                        if gift.price is None:
                            reasons.append("No price")
                        elif not (settings.price_limit_from <= gift.price <= settings.price_limit_to):
                            reasons.append(f"Price out of range")
                        if gift.total_count is None:
                            reasons.append("Unlimited gift")
                        elif settings.supply_limit and gift.total_count > settings.supply_limit:
                            reasons.append(f"Supply > limit")
                        if user.balance < (gift.price or 0):
                            reasons.append("Insufficient balance")
                        
                        if reasons:
                            status_text += f"  Reason: {', '.join(reasons)}\n"
            
            await message.answer(status_text, parse_mode="Markdown")
            
    except Exception as e:
        log.error(f"Error in check_autobuy_status: {e}")
        await message.answer(f"❌ Error: {str(e)}")