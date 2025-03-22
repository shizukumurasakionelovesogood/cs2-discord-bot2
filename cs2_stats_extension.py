import disnake
from disnake.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import re
import os
import sys
import logging
import random
import time

# Настройка логгирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CS2Stats')

class CS2Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.stats_channel_id = 1353080750362071131  # ID канала для статистики
        # Список User-Agent для ротации
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.last_request_time = 0
        self.rate_limit_delay = 5  # Минимальное время между запросами в секундах
    
    async def cog_load(self):
        # Создание aiohttp сессии при загрузке cog с правильными настройками
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        logger.info("✅ CS2 Stats extension загружен успешно!")
    
    async def cog_unload(self):
        # Закрытие aiohttp сессии при выгрузке cog
        if self.session:
            await self.session.close()
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"✅ CS2 Stats extension готов к использованию с {self.bot.user}!")
    
    def get_random_user_agent(self):
        """Выбирает случайный User-Agent из списка"""
        return random.choice(self.user_agents)
    
    async def fetch_page(self, url):
        """Получить HTML контент с URL с улучшенной обработкой ошибок и имитацией поведения браузера"""
        try:
            # Соблюдаем ограничение скорости запросов
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
            
            logger.info(f"Попытка получить данные с URL: {url}")
            
            # Заголовки, имитирующие обычный браузер
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://csstats.gg/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # Добавляем случайную задержку для имитации человеческого поведения
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Делаем запрос с нужными заголовками и cookie
            async with self.session.get(url, headers=headers, timeout=30, ssl=True) as response:
                self.last_request_time = time.time()  # Обновляем время последнего запроса
                
                if response.status == 200:
                    logger.info(f"Успешно получены данные с {url} (статус: 200)")
                    return await response.text()
                elif response.status == 403:
                    logger.error(f"Доступ запрещен (статус 403). Сайт, возможно, блокирует запросы.")
                    return None
                elif response.status == 429:
                    logger.error(f"Превышен лимит запросов (статус 429). Ждем 30 секунд.")
                    await asyncio.sleep(30)  # Ожидаем перед повторной попыткой при превышении лимита
                    return None
                else:
                    logger.error(f"Ошибка при получении данных: HTTP статус {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка клиента aiohttp: {e}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при запросе к {url}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при запросе: {e}")
            return None
    
    async def parse_cs_stats(self, steam_id):
        """Парсинг статистики CS2 с csstats.gg с улучшенной обработкой ошибок"""
        # Попробуем использовать альтернативный URL-формат, если основной не работает
        urls_to_try = [
            f"https://csstats.gg/player/{steam_id}",
            f"https://csstats.gg/ru/player/{steam_id}"  # Попробуем русскую версию как альтернативу
        ]
        
        html = None
        
        # Пробуем каждый URL последовательно
        for url in urls_to_try:
            html = await self.fetch_page(url)
            if html:
                logger.info(f"Успешно получены данные с {url}")
                break
            else:
                logger.warning(f"Не удалось получить данные с {url}, пробуем следующий URL...")
        
        if not html:
            logger.error(f"Не удалось получить HTML ни с одного из URL")
            return {
                "error": "Не удалось получить данные игрока. Возможные причины:\n"
                         "1. Сервис csstats.gg временно недоступен\n"
                         "2. Неверный Steam ID\n"
                         "3. Профиль игрока скрыт\n"
                         "Попробуйте позже или проверьте Steam ID."
            }
        
        try:
            logger.info(f"Начинаем парсинг HTML для {steam_id}")
            soup = BeautifulSoup(html, 'html.parser')
            
            # Проверка на наличие страницы ошибки
            error_container = soup.select_one('.error-container')
            if error_container:
                error_message = error_container.get_text().strip()
                logger.error(f"Ошибка на сайте: {error_message}")
                return {"error": f"Error from csstats.gg: {error_message}"}
            
            # Инициализация словаря статистики
            stats = {
                "profile_url": f"https://csstats.gg/player/{steam_id}",
                "matches_url": f"https://csstats.gg/player/{steam_id}#/matches",
                "player_name": "Unknown",
                "avatar_url": "",
                "win_rate": "N/A",
                "kd_ratio": "N/A",
                "headshot_percentage": "N/A",
                "premier_rank": "N/A",
                "highest_premier_rank": "N/A",
                "faceit_level": "N/A",
                "highest_faceit_level": "N/A"
            }
            
            # Извлечение имени игрока
            player_name_elem = soup.select_one('.headline-1')
            if player_name_elem:
                stats["player_name"] = player_name_elem.text.strip()
                logger.info(f"Найдено имя игрока: {stats['player_name']}")
            else:
                logger.warning("Не найден элемент с именем игрока")
            
            # Извлечение URL аватара
            avatar_elem = soup.select_one('.player-avatar img')
            if avatar_elem and 'src' in avatar_elem.attrs:
                stats["avatar_url"] = avatar_elem['src']
                logger.info(f"Найден URL аватара: {stats['avatar_url']}")
            else:
                logger.warning("Не найден элемент аватара")
            
            # Извлечение процента побед
            win_rate_elem = soup.select_one('.win-rate-percent')
            if win_rate_elem:
                stats["win_rate"] = win_rate_elem.text.strip()
                logger.info(f"Найден процент побед: {stats['win_rate']}")
            else:
                logger.warning("Не найден элемент процента побед")
            
            # Извлечение соотношения KD и процента хедшотов
            stat_boxes = soup.select('.stats-box')
            for box in stat_boxes:
                label_elem = box.select_one('.stats-box-label')
                value_elem = box.select_one('.stats-box-value')
                
                if not label_elem or not value_elem:
                    continue
                
                label = label_elem.text.strip().lower()
                value = value_elem.text.strip()
                
                if 'k/d' in label:
                    stats["kd_ratio"] = value
                    logger.info(f"Найден KD: {value}")
                elif 'headshot' in label:
                    stats["headshot_percentage"] = value
                    logger.info(f"Найден процент хедшотов: {value}")
            
            # Извлечение ранга Premier
            premier_elem = soup.select_one('.premier-rank-name')
            if premier_elem:
                stats["premier_rank"] = premier_elem.text.strip()
                logger.info(f"Найден ранг Premier: {stats['premier_rank']}")
            else:
                logger.warning("Не найден элемент ранга Premier")
            
            # Извлечение наивысшего ранга Premier
            highest_premier_elem = soup.select_one('.premier-rank-highest')
            if highest_premier_elem:
                highest_text = highest_premier_elem.text.strip()
                highest_match = re.search(r'Highest: (.+)', highest_text)
                if highest_match:
                    stats["highest_premier_rank"] = highest_match.group(1)
                    logger.info(f"Найден наивысший ранг Premier: {stats['highest_premier_rank']}")
            else:
                logger.warning("Не найден элемент наивысшего ранга Premier")
            
            # Извлечение уровня Faceit
            faceit_elem = soup.select_one('.faceit-level')
            if faceit_elem:
                stats["faceit_level"] = faceit_elem.text.strip() 
                logger.info(f"Найден уровень Faceit: {stats['faceit_level']}")
            else:
                logger.warning("Не найден элемент уровня Faceit")
            
            # Извлечение наивысшего уровня Faceit
            highest_faceit_elem = soup.select_one('.faceit-level-highest')
            if highest_faceit_elem:
                highest_text = highest_faceit_elem.text.strip()
                highest_match = re.search(r'Highest: (.+)', highest_text)
                if highest_match:
                    stats["highest_faceit_level"] = highest_match.group(1)
                    logger.info(f"Найден наивысший уровень Faceit: {stats['highest_faceit_level']}")
            else:
                logger.warning("Не найден элемент наивысшего уровня Faceit")
            
            # Проверяем, что мы смогли извлечь хотя бы основную статистику
            # Если HTML был получен, но данные не найдены, возможно структура сайта изменилась
            if stats["player_name"] == "Unknown" and stats["win_rate"] == "N/A" and stats["kd_ratio"] == "N/A":
                logger.error("Получен HTML, но не удалось извлечь данные. Возможно, структура сайта изменилась.")
                return {
                    "error": "Получен ответ от сервера, но не удалось найти данные игрока.\n"
                              "Возможно, профиль не существует или структура сайта изменилась."
                }
            
            logger.info(f"Парсинг завершен успешно для {steam_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"Ошибка при обработке данных игрока: {str(e)}"}
    
    # Проверка валидности Steam ID
    def validate_steam_id(self, steam_id):
        """Проверяет валидность Steam ID и извлекает его из URL"""
        # Извлечение Steam ID из URL, если необходимо
        if "steamcommunity.com" in steam_id:
            # Паттерн для URLs вида steamcommunity.com/profiles/XXXXXXXXX
            profile_match = re.search(r'steamcommunity\.com/profiles/(\d+)', steam_id)
            if profile_match:
                steam_id = profile_match.group(1)
                logger.info(f"Извлечен числовой Steam ID из URL профиля: {steam_id}")
                return steam_id, None
            
            # Паттерн для URLs вида steamcommunity.com/id/customname
            id_match = re.search(r'steamcommunity\.com/id/([^/]+)', steam_id)
            if id_match:
                custom_id = id_match.group(1)
                logger.info(f"Извлечен кастомный Steam ID из URL: {custom_id}")
                return custom_id, None
        
        # Проверка валидности SteamID (числовой или кастомный ID)
        if steam_id.isdigit():
            # Числовой SteamID должен быть достаточно длинным
            if len(steam_id) < 5:
                return None, "Steam ID слишком короткий. Пожалуйста, укажите корректный Steam ID или URL профиля."
            return steam_id, None
        elif re.match(r'^[a-zA-Z0-9_-]+$', steam_id):
            # Кастомный ID должен содержать только допустимые символы
            return steam_id, None
        else:
            return None, "Неверный формат Steam ID. Пожалуйста, укажите корректный Steam ID или URL профиля."
    
    @commands.slash_command(
        name="cs2stats",
        description="Получить статистику CS2 игрока с csstats.gg",
        guild_ids=[994523162148601886]  # ID вашего сервера
    )
    async def cs2stats(
        self,
        inter,
        steam_id: str = commands.Param(
            description="Steam ID или URL профиля (например, 76561199591409529 или полный URL профиля)"
        )
    ):
        await inter.response.defer()
        
        # Валидация Steam ID
        validated_id, error = self.validate_steam_id(steam_id)
        if error:
            logger.warning(f"Невалидный формат Steam ID: {steam_id}")
            return await inter.followup.send(error)
        
        steam_id = validated_id
        
        # Получение и парсинг статистики
        logger.info(f"Получаем статистику для {steam_id}")
        stats = await self.parse_cs_stats(steam_id)
        
        if "error" in stats:
            logger.error(f"Ошибка при получении статистики: {stats['error']}")
            return await inter.followup.send(f"❌ **Ошибка:** {stats['error']}")
        
        # Создание эмбеда
        embed = disnake.Embed(
            title=f"CS2 статистика для {stats['player_name']}",
            url=stats['profile_url'],
            color=disnake.Color.blue()
        )
        
        if stats['avatar_url']:
            embed.set_thumbnail(url=stats['avatar_url'])
        
        # Добавление основной статистики
        embed.add_field(name="Процент побед", value=stats['win_rate'], inline=True)
        embed.add_field(name="K/D", value=stats['kd_ratio'], inline=True)
        embed.add_field(name="Хедшоты %", value=stats['headshot_percentage'], inline=True)
        
        # Добавление информации о рангах
        embed.add_field(name="Ранг Premier", value=stats['premier_rank'], inline=True)
        embed.add_field(name="Высший Premier", value=stats['highest_premier_rank'], inline=True)
        embed.add_field(name="Уровень Faceit", value=stats['faceit_level'], inline=True)
        
        # Добавление ссылки на матчи
        embed.add_field(
            name="История матчей",
            value=f"[Посмотреть все матчи]({stats['matches_url']})",
            inline=False
        )
        
        embed.set_footer(text="Данные с csstats.gg | Статистика может быть не 100% точной")
        
        logger.info(f"Отправка эмбеда с статистикой для {steam_id}")
        await inter.followup.send(embed=embed)
    
    @commands.slash_command(
        name="trackcs2",
        description="Отслеживать профиль игрока CS2 в выделенном канале",
        guild_ids=[994523162148601886]  # ID вашего сервера
    )
    async def trackcs2(
        self,
        inter,
        steam_id: str = commands.Param(
            description="Steam ID или URL профиля"
        ),
        nickname: str = commands.Param(
            description="Опциональный никнейм для идентификации игрока",
            default=None
        )
    ):
        await inter.response.defer()
        
        # Валидация Steam ID
        validated_id, error = self.validate_steam_id(steam_id)
        if error:
            logger.warning(f"Невалидный формат Steam ID: {steam_id}")
            return await inter.followup.send(error)
        
        steam_id = validated_id
        
        # Получение статистики один раз для проверки
        logger.info(f"Проверка статистики для {steam_id} перед отслеживанием")
        stats = await self.parse_cs_stats(steam_id)
        
        if "error" in stats:
            logger.error(f"Ошибка при получении статистики: {stats['error']}")
            return await inter.followup.send(f"❌ **Ошибка:** {stats['error']}")
        
        # Получение канала
        channel = self.bot.get_channel(self.stats_channel_id)
        if not channel:
            logger.error(f"Не удалось найти канал для статистики (ID: {self.stats_channel_id})")
            return await inter.followup.send(f"❌ **Ошибка:** Не удалось найти канал для статистики (ID: {self.stats_channel_id})")
        
        # Создание эмбеда
        player_name = nickname or stats['player_name']
        embed = disnake.Embed(
            title=f"CS2 игрок отслеживается: {player_name}",
            description=f"Steam ID: {steam_id}\nПрофиль: [csstats.gg]({stats['profile_url']})",
            color=disnake.Color.green()
        )
        
        if stats['avatar_url']:
            embed.set_thumbnail(url=stats['avatar_url'])
        
        embed.set_footer(text="Используйте /cs2stats для получения подробной статистики")
        
        logger.info(f"Отслеживание профиля {player_name} в канале {self.stats_channel_id}")
        await channel.send(embed=embed)
        await inter.followup.send(f"✅ Успешно начато отслеживание профиля {player_name} в канале <#{self.stats_channel_id}>!")

def setup(bot):
    bot.add_cog(CS2Stats(bot))