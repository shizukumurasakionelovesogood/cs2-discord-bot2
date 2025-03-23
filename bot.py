import disnake
from disnake.ext import commands
import asyncio
from collections import defaultdict
import random
from cs2_player_tracker import CS2PlayerTracker
from yes_no_game import YesNoGame
import os
from dotenv import load_dotenv
import http.server
import threading

# Загружаем переменные окружения
load_dotenv()

# Создаем бота
intents = disnake.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.InteractionBot(intents=intents)

# Словарь для хранения счета игроков
player_scores = defaultdict(int)

# Словарь для хранения активных игр
active_games = {}

# Инициализация CS2 трекера
tracker = CS2PlayerTracker()

# Инициализация игры "Да или Нет"
yes_no_game = YesNoGame()

# ID канала для уведомлений
NOTIFICATION_CHANNEL_ID = 1353101922227191962

async def check_players_status():
    while True:
        messages = tracker.check_players_status()
        for chat_id, message in messages:
            try:
                channel = bot.get_channel(chat_id)
                if channel:
                    await channel.send(message)
            except Exception as e:
                print(f"Ошибка отправки сообщения: {e}")
        await asyncio.sleep(30)  # Проверка каждые 30 секунд

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} успешно запущен!")
    # Запускаем проверку статуса игроков
    bot.loop.create_task(check_players_status())

@bot.event
async def on_member_join(member):
    guild = member.guild
    role = disnake.utils.get(guild.roles, id=1353051664067727531)  # Укажи свой ID роли
    if role:
        try:
            await member.add_roles(role)
            print(f"✅ Назначена роль {role.name} для {member.name}")
        except disnake.Forbidden:
            print("❌ Ошибка: у бота недостаточно прав!")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
    else:
        print("❌ Роль не найдена!")

@bot.event
async def on_message(message):
    # Игнорируем сообщения от ботов
    if message.author.bot:
        return
    
    # Проверяем, есть ли активная игра
    if not active_games:
        return
    
    # Проверяем, что сообщение отправлено в игровой канал
    game_channel_id = 1353043535468826705
    if message.channel.id != game_channel_id:
        return
    
    # Проверяем, что сообщение - "я" (регистронезависимо)
    if message.content.lower() == "я":
        game_id = list(active_games.keys())[-1]
        game = active_games[game_id]
        
        # Проверяем, что игрок еще не присоединился к игре
        if message.author.id in game["joined_players"]:
            await message.channel.send(f"{message.author.mention}, вы уже присоединились к игре!", delete_after=5)
            return
        
        # Добавляем игрока в список присоединившихся
        game["joined_players"].append(message.author.id)
        await message.channel.send(f"🎮 {message.author.mention} присоединился к игре! Всего игроков: {len(game['joined_players'])}")

# Команда для генерации случайного числа
@bot.slash_command(
    name="randomnumber",
    description="Сгенерировать случайное число в заданном диапазоне",
    guild_ids=[994523162148601886]
)
async def randomnumber(
    inter,
    min_number: int = commands.Param(
        description="Минимальное число диапазона",
        default=1
    ),
    max_number: int = commands.Param(
        description="Максимальное число диапазона",
        ge=2,  # Минимальное значение 2
        le=1000000  # Максимальное значение 1000000
    )
):
    # Проверка, что команда запущена в правильном канале
    game_channel_id = 1353043535468826705  # ID игрового канала
    
    if inter.channel.id != game_channel_id:
        return await inter.response.send_message(
            f"Команда доступна только в <#{game_channel_id}>!",
            ephemeral=True
        )
    
    # Проверяем корректность диапазона
    if min_number >= max_number:
        return await inter.response.send_message(
            "Ошибка: минимальное число должно быть меньше максимального!",
            ephemeral=True
        )
    
    # Генерируем случайное число
    random_number = random.randint(min_number, max_number)
    
    await inter.response.send_message(
        f"🎲 {inter.author.mention} запросил случайное число от {min_number} до {max_number}.\n"
        f"**Результат: {random_number}**"
    )

@bot.slash_command(
    name="execution",
    description="Отправить сообщение об успешном выполнении",
    guild_ids=[994523162148601886]
)
async def execution(inter):
    channel_id = 1353043535468826705
   
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("хуй отрезан успешно ✅")
        await inter.response.send_message("Уведомление отправлено!")
    else:
        await inter.response.send_message("Канал не найден!", ephemeral=True)

# Команда для начала игры Камень-Ножницы-Бумага
@bot.slash_command(
    name="startgame",
    description="Начать игру в Камень-Ножницы-Бумага",
    guild_ids=[994523162148601886]
)
async def startgame(inter):
    # Проверка, что игра запущена в правильном канале
    game_channel_id = 1353043535468826705  # Замените на ID вашего игрового канала
    
    if inter.channel.id != game_channel_id:
        return await inter.response.send_message(
            f"Игра доступна только в <#{game_channel_id}>!", 
            ephemeral=True
        )
    
    # Проверка, что нет активной игры
    if active_games:
        return await inter.response.send_message(
            "Уже есть активная игра! Дождитесь её окончания.",
            ephemeral=True
        )
    
    # Создаем новую игру
    game_id = str(inter.id)
    active_games[game_id] = {
        "players": {},
        "joined_players": [inter.author.id],  # Список игроков, присоединившихся к игре
        "timeout": 30,  # Таймаут игры в секундах
        "created_by": inter.author.id,
        "channel": inter.channel,
        "status": "waiting"  # Статус игры: waiting (ожидание игроков), started (игра началась)
    }
    
    await inter.response.send_message(
        f"🎮 {inter.author.mention} начал игру в Камень-Ножницы-Бумага!\n"
        f"Присоединяйтесь к игре, написав **я** в этом канале.\n"
        f"У вас есть 30 секунд, чтобы присоединиться.\n"
        f"Создатель игры может начать игру командой `/startmatch`\n"
        f"или игра начнется автоматически через 30 секунд."
    )
    
    # Запускаем таймер игры
    timeout_task = asyncio.create_task(game_timeout(game_id, inter.channel))
    active_games[game_id]["timeout_task"] = timeout_task

# Функция для обработки таймаута игры
async def game_timeout(game_id, channel):
    await asyncio.sleep(active_games[game_id]["timeout"])
    
    # Проверяем, есть ли игра еще в списке активных
    if game_id in active_games:
        game = active_games[game_id]
        
        # Если статус все еще "waiting", начинаем игру автоматически
        if game["status"] == "waiting":
            # Проверяем, достаточно ли игроков
            if len(game["joined_players"]) < 2:
                await channel.send("⏱️ Время вышло! Игра отменена из-за недостатка игроков (нужно минимум 2).")
                del active_games[game_id]
                return
            
            # Меняем статус игры
            game["status"] = "started"
            
            # Начинаем игру
            await channel.send(f"⏱️ Время ожидания истекло! Игра начинается с {len(game['joined_players'])} игроками!")
            await start_match(channel, game_id)

# Команда для ручного запуска игры создателем
@bot.slash_command(
    name="startmatch",
    description="Начать матч с присоединившимися игроками",
    guild_ids=[994523162148601886]
)
async def startmatch(inter):
    # Проверка, что игра запущена в правильном канале
    game_channel_id = 1353043535468826705
    
    if inter.channel.id != game_channel_id:
        return await inter.response.send_message(
            f"Игра доступна только в <#{game_channel_id}>!", 
            ephemeral=True
        )
    
    # Проверка, есть ли активная игра
    if not active_games:
        return await inter.response.send_message(
            "Сейчас нет активной игры! Используйте `/startgame` чтобы начать игру.",
            ephemeral=True
        )
    
    game_id = list(active_games.keys())[-1]
    game = active_games[game_id]
    
    # Проверка, что команду вызвал создатель игры
    if inter.author.id != game["created_by"]:
        return await inter.response.send_message(
            "Только создатель игры может начать матч!",
            ephemeral=True
        )
    
    # Проверка, что игра все еще в режиме ожидания
    if game["status"] != "waiting":
        return await inter.response.send_message(
            "Игра уже началась!",
            ephemeral=True
        )
    
    # Проверка, что есть достаточно игроков
    if len(game["joined_players"]) < 2:
        return await inter.response.send_message(
            "Недостаточно игроков для начала матча (нужно минимум 2)!",
            ephemeral=True
        )
    
    # Отменяем таймаут, если он еще активен
    if "timeout_task" in game and not game["timeout_task"].done():
        game["timeout_task"].cancel()
    
    # Меняем статус игры
    game["status"] = "started"
    
    await inter.response.send_message(f"🎲 Матч начинается с {len(game['joined_players'])} игроками!")
    
    # Запускаем матч
    await start_match(inter.channel, game_id)

# Функция для запуска матча
async def start_match(channel, game_id):
    game = active_games[game_id]
    
    # Отправляем сообщение о начале матча и инструкции
    await channel.send(
        "🎯 **Матч начался!**\n"
        "У вас есть 30 секунд, чтобы сделать свой выбор.\n"
        "Используйте следующие команды для игры:\n"
        "- `/rock` для выбора камня 🪨\n"
        "- `/paper` для выбора бумаги 📄\n"
        "- `/scissors` для выбора ножниц ✂️"
    )
    
    # Создаем таймер для окончания матча
    match_timer = asyncio.create_task(match_timeout(game_id, channel))
    active_games[game_id]["match_timer"] = match_timer

# Функция для обработки таймаута матча
async def match_timeout(game_id, channel):
    await asyncio.sleep(30)  # Даем 30 секунд на выбор
    
    # Проверяем, есть ли игра еще в списке активных
    if game_id in active_games:
        game = active_games[game_id]
        
        # Получаем игроков, которые сделали свой выбор
        players_made_choice = list(game["players"].keys())
        
        # Если никто не сделал выбор, отменяем игру
        if len(players_made_choice) == 0:
            await channel.send("⏱️ Никто не сделал выбор! Игра отменена.")
            del active_games[game_id]
            return
        
        # Если только один игрок сделал выбор, он побеждает по умолчанию
        if len(players_made_choice) == 1:
            player_id = players_made_choice[0]
            player = bot.get_user(player_id)
            
            await channel.send(f"⏱️ Только {player.mention} сделал выбор! Победа по умолчанию!")
            player_scores[player_id] += 1
            
            await channel.send(f"🏆 {player.mention} побеждает! (Всего побед: {player_scores[player_id]})")
            
            del active_games[game_id]
            return
        
        # Если несколько игроков сделали выбор, определяем победителя
        await determine_winners(channel, game_id)

# Функция для определения победителей
async def determine_winners(channel, game_id):
    if game_id not in active_games:
        return
    
    game = active_games[game_id]
    players = game["players"]
    
    # Если меньше 2 игроков сделали выбор, отменяем функцию
    # (это не должно произойти, так как match_timeout уже проверяет это)
    if len(players) < 2:
        return
    
    # Отменяем таймер матча, если он еще активен
    if "match_timer" in game and not game["match_timer"].done():
        game["match_timer"].cancel()
    
    # Сообщаем, что скоро будут результаты
    await channel.send("⏳ Результаты будут объявлены через 10 секунд...")
    
    # Ждем 10 секунд перед объявлением результатов
    await asyncio.sleep(10)
    
    # Собираем данные о выборах игроков
    choices_info = []
    for player_id, choice in players.items():
        player = bot.get_user(player_id)
        choices_info.append(f"{player.mention}: {get_emoji(choice)} {choice.capitalize()}")
    
    # Показываем выборы игроков
    await channel.send("Выборы игроков:\n" + "\n".join(choices_info))
    
    # Определяем победителей
    # Для каждого игрока считаем количество побед над другими игроками
    win_counts = defaultdict(int)
    
    player_ids = list(players.keys())
    
    # Сравниваем каждого игрока с каждым
    for i in range(len(player_ids)):
        for j in range(i + 1, len(player_ids)):
            player1_id = player_ids[i]
            player2_id = player_ids[j]
            
            player1_choice = players[player1_id]
            player2_choice = players[player2_id]
            
            # Если ничья, никто не получает очко
            if player1_choice == player2_choice:
                continue
            
            # Если первый игрок побеждает второго
            if beats(player1_choice, player2_choice):
                win_counts[player1_id] += 1
            else:
                win_counts[player2_id] += 1
    
    # Находим игрока(ов) с максимальным количеством побед
    if not win_counts:
        # Если все выбрали одно и то же, ничья
        await channel.send("🤝 Ничья! Все игроки выбрали одинаковый предмет.")
    else:
        max_wins = max(win_counts.values())
        winners = [player_id for player_id, wins in win_counts.items() if wins == max_wins]
        
        # Если есть несколько победителей с одинаковым счетом
        if len(winners) > 1:
            winners_mentions = [bot.get_user(w_id).mention for w_id in winners]
            await channel.send(f"🏆 Ничья между: {', '.join(winners_mentions)}! У всех по {max_wins} побед.")
            
            # Всем победителям добавляем по одному очку
            for winner_id in winners:
                player_scores[winner_id] += 1
        else:
            # Один победитель
            winner_id = winners[0]
            winner = bot.get_user(winner_id)
            player_scores[winner_id] += 1
            
            await channel.send(f"🏆 Победил {winner.mention} с {max_wins} победами! (Всего побед: {player_scores[winner_id]})")
    
    # Удаляем игру из активных
    del active_games[game_id]

# Функция для получения эмодзи для выбора
def get_emoji(choice):
    if choice == "rock":
        return "🪨"
    elif choice == "paper":
        return "📄"
    elif choice == "scissors":
        return "✂️"
    return ""

# Функция для определения победителя между двумя выборами
def beats(choice1, choice2):
    if choice1 == "rock":
        return choice2 == "scissors"
    elif choice1 == "paper":
        return choice2 == "rock"
    elif choice1 == "scissors":
        return choice2 == "paper"
    return False

# Команды для выбора в игре
@bot.slash_command(
    name="rock",
    description="Выбрать камень в игре",
    guild_ids=[994523162148601886]
)
async def rock(inter):
    await make_choice(inter, "rock", "🪨 Камень")

@bot.slash_command(
    name="paper",
    description="Выбрать бумагу в игре",
    guild_ids=[994523162148601886]
)
async def paper(inter):
    await make_choice(inter, "paper", "📄 Бумага")

@bot.slash_command(
    name="scissors",
    description="Выбрать ножницы в игре",
    guild_ids=[994523162148601886]
)
async def scissors(inter):
    await make_choice(inter, "scissors", "✂️ Ножницы")

# Функция для обработки выбора игрока
async def make_choice(inter, choice, choice_name):
    # Проверка, что игра запущена в правильном канале
    game_channel_id = 1353043535468826705  # Замените на ID вашего игрового канала
    
    if inter.channel.id != game_channel_id:
        return await inter.response.send_message(
            f"Игра доступна только в <#{game_channel_id}>!", 
            ephemeral=True
        )
    
    # Проверка, есть ли активная игра
    if not active_games:
        return await inter.response.send_message(
            "Сейчас нет активной игры! Используйте `/startgame` чтобы начать игру.",
            ephemeral=True
        )
    
    # Берем последнюю созданную игру
    game_id = list(active_games.keys())[-1]
    game = active_games[game_id]
    
    # Проверка, что игра уже началась
    if game["status"] != "started":
        return await inter.response.send_message(
            "Игра еще не началась! Дождитесь начала игры.",
            ephemeral=True
        )
    
    # Проверка, что игрок присоединился к игре
    if inter.author.id not in game["joined_players"]:
        return await inter.response.send_message(
            "Вы не присоединились к этой игре!",
            ephemeral=True
        )
    
    # Проверка, делал ли игрок уже выбор
    if inter.author.id in game["players"]:
        return await inter.response.send_message(
            "Вы уже сделали свой выбор в этой игре!",
            ephemeral=True
        )
    
    # Записываем выбор игрока
    game["players"][inter.author.id] = choice
    await inter.response.send_message(
        f"Вы выбрали {choice_name}. Ожидайте окончания игры!",
        ephemeral=True
    )
    
    # Сообщаем всем, что игрок сделал выбор (без раскрытия самого выбора)
    await inter.channel.send(f"{inter.author.mention} сделал свой выбор!")
    
    # Проверяем, все ли игроки сделали выбор
    if len(game["players"]) == len(game["joined_players"]):
        # Если все сделали выбор, отменяем таймер и сразу определяем победителя
        if "match_timer" in game and not game["match_timer"].done():
            game["match_timer"].cancel()
        
        await inter.channel.send("✨ Все игроки сделали свой выбор!")
        await determine_winners(inter.channel, game_id)

# Команда для просмотра счета
@bot.slash_command(
    name="score",
    description="Посмотреть счет игроков",
    guild_ids=[994523162148601886]
)
async def score(inter):
    # Сортируем игроков по количеству побед
    sorted_scores = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Формируем сообщение со счетом
    score_message = "🏆 **Таблица лидеров:**\n"
    
    # Проверяем, есть ли победы у игроков
    if not sorted_scores:
        score_message += "Пока никто не побеждал в играх!\n"
        # Добавляем пустые места до 10
        for i in range(1, 11):
            score_message += f"{i}. -\n"
    else:
        # Выводим существующих победителей
        for i in range(1, 11):
            if i <= len(sorted_scores):
                player_id, score = sorted_scores[i-1]
                player = bot.get_user(player_id)
                player_name = player.name if player else f"Игрок {player_id}"
                score_message += f"{i}. {player_name}: {score} побед\n"
            else:
                # Добавляем пустые места, если победителей меньше 10
                score_message += f"{i}. -\n"
    
    await inter.response.send_message(score_message)

# Команда для отмены игры
@bot.slash_command(
    name="cancelgame",
    description="Отменить текущую игру",
    guild_ids=[994523162148601886]
)
async def cancelgame(inter):
    if not active_games:
        return await inter.response.send_message("Сейчас нет активных игр!", ephemeral=True)
    
    game_id = list(active_games.keys())[-1]
    game = active_games[game_id]
    
    # Только создатель игры или администратор может отменить игру
    if inter.author.id != game["created_by"] and not inter.author.guild_permissions.administrator:
        return await inter.response.send_message(
            "Только создатель игры или администратор может отменить игру!",
            ephemeral=True
        )
    
    # Отменяем таймауты
    if "timeout_task" in game and not game["timeout_task"].done():
        game["timeout_task"].cancel()
    
    if "match_timer" in game and not game["match_timer"].done():
        game["match_timer"].cancel()
    
    # Удаляем игру
    del active_games[game_id]
    
    await inter.response.send_message("🛑 Игра была отменена!")

# Команда для регистрации токенов
@bot.slash_command(
    name="register_tokens",
    description="Зарегистрировать токены для отслеживания CS2",
    guild_ids=[994523162148601886]
)
async def register_tokens(
    inter,
    match_token: str = commands.Param(description="Match Token"),
    auth_code: str = commands.Param(description="Authentication Code"),
    steam_api_key: str = commands.Param(description="Steam API Key")
):
    result = tracker.register_tokens(match_token, auth_code, steam_api_key, inter.author.id)
    await inter.response.send_message(result, ephemeral=True)

# Команда для просмотра информации о токенах
@bot.slash_command(
    name="token_info",
    description="Показать информацию о зарегистрированных токенах",
    guild_ids=[994523162148601886]
)
async def token_info(inter):
    token_info = tracker.get_token_info()
    if token_info:
        user_id, registration_time = token_info
        user = bot.get_user(user_id)
        user_name = user.name if user else f"Пользователь {user_id}"
        
        embed = disnake.Embed(
            title="Информация о токенах",
            color=disnake.Color.blue()
        )
        embed.add_field(
            name="Зарегистрировал",
            value=f"{user_name}",
            inline=False
        )
        embed.add_field(
            name="Дата регистрации",
            value=registration_time.strftime("%d.%m.%Y %H:%M:%S"),
            inline=False
        )
        
        await inter.response.send_message(embed=embed, ephemeral=True)
    else:
        await inter.response.send_message(
            "Токены еще не были зарегистрированы!",
            ephemeral=True
        )

# Команда для добавления игрока
@bot.slash_command(
    name="add_player",
    description="Добавить игрока для отслеживания",
    guild_ids=[994523162148601886]
)
async def add_player(
    inter,
    steam_id: str = commands.Param(description="Steam ID игрока")
):
    result = tracker.add_player_to_monitor(steam_id, NOTIFICATION_CHANNEL_ID)
    await inter.response.send_message(result, ephemeral=True)

# Команда для удаления игрока
@bot.slash_command(
    name="remove_player",
    description="Удалить игрока из отслеживания",
    guild_ids=[994523162148601886]
)
async def remove_player(
    inter,
    steam_id: str = commands.Param(description="Steam ID игрока")
):
    result = tracker.remove_player_from_monitor(steam_id)
    await inter.response.send_message(result, ephemeral=True)

# Команда для просмотра списка отслеживаемых игроков
@bot.slash_command(
    name="list_players",
    description="Показать список отслеживаемых игроков",
    guild_ids=[994523162148601886]
)
async def list_players(inter):
    players = tracker.get_monitored_players()
    if players:
        response = "Отслеживаемые игроки:\n" + "\n".join(players)
    else:
        response = "Список отслеживаемых игроков пуст"
    await inter.response.send_message(response, ephemeral=True)

# Функция для запуска HTTP сервера
def run_http_server():
    port = int(os.getenv('PORT', 8000))
    server = http.server.HTTPServer(('0.0.0.0', port), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()

# Запуск HTTP сервера в отдельном потоке
http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()

@bot.slash_command(name="yesno", description="Начать игру 'Да или Нет'")
async def yesno(inter: disnake.ApplicationCommandInteraction):
    question = yes_no_game.get_random_question()
    
    # Создаем кнопки
    buttons = disnake.ui.ActionRow(
        disnake.ui.Button(label="Да", style=disnake.ButtonStyle.green, custom_id="yes"),
        disnake.ui.Button(label="Нет", style=disnake.ButtonStyle.red, custom_id="no")
    )
    
    # Отправляем вопрос в указанный канал
    channel = bot.get_channel(1353364406293106759)
    await channel.send(
        f"🎮 Игра 'Да или Нет' от {inter.author.mention}\n"
        f"❓ {question['question']}\n"
        f"📚 Категория: {question['category']}",
        components=[buttons]
    )
    
    # Отправляем подтверждение игроку
    await inter.response.send_message("Вопрос отправлен в канал игры!", ephemeral=True)
    
    # Сохраняем вопрос для проверки ответа
    active_games[inter.id] = question

@bot.slash_command(name="stats", description="Показать вашу статистику в игре 'Да или Нет'")
async def stats(inter: disnake.ApplicationCommandInteraction):
    stats_text = yes_no_game.get_player_stats(str(inter.author.id))
    await inter.response.send_message(stats_text, ephemeral=True)

@bot.slash_command(name="top", description="Показать топ-3 игроков в игре 'Да или Нет'")
async def top(inter: disnake.ApplicationCommandInteraction):
    top_players = yes_no_game.get_top_players()
    
    if not top_players:
        await inter.response.send_message("Пока нет игроков в топе. Сыграйте несколько игр! (Статистика сохраняется между сессиями)")
        return
    
    response = "🏆 Топ-3 игроков (сохраняется между сессиями):\n\n"
    for i, player in enumerate(top_players, 1):
        user = await bot.fetch_user(int(player["id"]))
        response += f"{i}. {user.name}: {player['points']} очков ({player['accuracy']:.1f}%)\n"
    
    await inter.response.send_message(response)

@bot.event
async def on_button_click(inter: disnake.MessageInteraction):
    if inter.component.custom_id in ["yes", "no"]:
        if inter.message.interaction.id not in active_games:
            await inter.response.send_message("Игра уже закончена!", ephemeral=True)
            return
        
        question = active_games[inter.message.interaction.id]
        answer = "да" if inter.component.custom_id == "yes" else "нет"
        
        correct = yes_no_game.check_answer(question, answer, str(inter.author.id))
        
        # Отключаем кнопки
        buttons = disnake.ui.ActionRow(
            disnake.ui.Button(label="Да", style=disnake.ButtonStyle.green, custom_id="yes", disabled=True),
            disnake.ui.Button(label="Нет", style=disnake.ButtonStyle.red, custom_id="no", disabled=True)
        )
        
        # Обновляем сообщение в канале
        await inter.message.edit(components=[buttons])
        
        # Отправляем результат в канал
        channel = bot.get_channel(1353364406293106759)
        result_emoji = "✅" if correct else "❌"
        result_text = "правильно" if correct else "неправильно"
        await channel.send(
            f"{result_emoji} {inter.author.mention} ответил {result_text}!\n"
            f"Правильный ответ: {question['answer']}"
        )
        
        # Отправляем результат игроку
        if correct:
            await inter.response.send_message("✅ Правильно!", ephemeral=True)
        else:
            await inter.response.send_message(f"❌ Неправильно! Правильный ответ: {question['answer']}", ephemeral=True)
        
        # Удаляем вопрос из активных игр
        del active_games[inter.message.interaction.id]

# Запуск бота
bot.run(os.getenv('DISCORD_TOKEN'))