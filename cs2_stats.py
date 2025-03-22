import aiohttp
import asyncio

API_URL = "https://api.example.com/cs2/stats"  # Замените на реальный URL API

async def get_player_stats(player_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/{player_id}") as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

async def main():
    player_id = "example_player_id"  # Замените на реальный ID игрока
    stats = await get_player_stats(player_id)
    if stats:
        print(stats)
    else:
        print("Не удалось получить статистику игрока")

if __name__ == "__main__":
    asyncio.run(main())
