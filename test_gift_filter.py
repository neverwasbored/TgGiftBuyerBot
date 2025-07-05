# test_gift_filter.py
import asyncio
import aiohttp
from api.gifts import GiftsApi
from config import load_config

async def test_gift_filtering():
    """
    Тестирует фильтрацию unlimited подарков
    """
    config = load_config()
    gifts_api = GiftsApi()
    
    print("🔍 Testing gift filtering...\n")
    
    async with aiohttp.ClientSession() as session:
        # Получаем все подарки
        all_gifts = await gifts_api.aio_get_available_gifts(session)
        
        if not all_gifts:
            print("❌ No gifts received from API")
            return
        
        print(f"📊 Total gifts from API: {len(all_gifts)}")
        
        # Фильтруем
        limited_gifts = []
        unlimited_gifts = []
        
        for gift in all_gifts:
            gift_id = gift.get('id')
            price = gift.get('star_count')
            total = gift.get('total_count')
            remaining = gift.get('remaining_count')
            emoji = gift.get('sticker', {}).get('emoji', '🎁')
            
            if total is None or remaining is None:
                unlimited_gifts.append({
                    'id': gift_id,
                    'price': price,
                    'emoji': emoji,
                    'total': total,
                    'remaining': remaining
                })
            else:
                limited_gifts.append({
                    'id': gift_id,
                    'price': price,
                    'emoji': emoji,
                    'total': total,
                    'remaining': remaining
                })
        
        print(f"\n✅ LIMITED gifts (will be shown): {len(limited_gifts)}")
        print(f"❌ UNLIMITED gifts (will be hidden): {len(unlimited_gifts)}")
        
        # Показываем примеры
        print("\n🎁 LIMITED GIFT EXAMPLES (first 10):")
        for gift in limited_gifts[:10]:
            print(f"  • {gift['emoji']} ID: {gift['id']} | "
                  f"{gift['price']}⭐ | {gift['remaining']}/{gift['total']}")
        
        if len(limited_gifts) > 10:
            print(f"  ... and {len(limited_gifts) - 10} more")
        
        print("\n🚫 UNLIMITED GIFT EXAMPLES (first 10):")
        for gift in unlimited_gifts[:10]:
            print(f"  • {gift['emoji']} ID: {gift['id']} | "
                  f"{gift['price']}⭐ | Unlimited")
        
        if len(unlimited_gifts) > 10:
            print(f"  ... and {len(unlimited_gifts) - 10} more")
        
        # Статистика по ценам
        if limited_gifts:
            limited_prices = [g['price'] for g in limited_gifts]
            print(f"\n💰 LIMITED GIFTS PRICE STATS:")
            print(f"  • Min: {min(limited_prices)}⭐")
            print(f"  • Max: {max(limited_prices)}⭐")
            print(f"  • Average: {sum(limited_prices) / len(limited_prices):.1f}⭐")
        
        # Проверяем фильтрацию
        print(f"\n🧪 FILTER TEST:")
        test_gifts = all_gifts[:5]  # Берем первые 5 для теста
        
        for gift in test_gifts:
            total = gift.get('total_count')
            remaining = gift.get('remaining_count')
            
            # Применяем логику фильтрации
            is_unlimited = total is None or remaining is None
            
            print(f"\nGift {gift.get('id')}:")
            print(f"  • total_count: {total}")
            print(f"  • remaining_count: {remaining}")
            print(f"  • Is unlimited? {is_unlimited}")
            print(f"  • Will be shown? {'NO ❌' if is_unlimited else 'YES ✅'}")

if __name__ == "__main__":
    asyncio.run(test_gift_filtering())