import requests
import time
from datetime import datetime
import json
from typing import Dict, Optional
import os

class CS2PlayerTracker:
    def __init__(self):
        self.match_token = None
        self.auth_code = None
        self.steam_api_key = None
        self.last_match_id = None
        self.monitored_players: Dict[str, bool] = {}  # steam_id -> was_in_game
        self.chat_ids: Dict[str, int] = {}  # steam_id -> chat_id
        self.token_registered_by = None  # ID пользователя, зарегистрировавшего токены
        self.token_registration_time = None  # Время регистрации токенов
        self.config_file = "cs2_tracker_config.json"
        self.load_config()

    def save_config(self):
        config = {
            "match_token": self.match_token,
            "auth_code": self.auth_code,
            "steam_api_key": self.steam_api_key,
            "token_registered_by": self.token_registered_by,
            "token_registration_time": self.token_registration_time.isoformat() if self.token_registration_time else None,
            "monitored_players": self.monitored_players,
            "chat_ids": self.chat_ids
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        print("[DEBUG] Конфигурация сохранена")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.match_token = config.get("match_token")
                self.auth_code = config.get("auth_code")
                self.steam_api_key = config.get("steam_api_key")
                self.token_registered_by = config.get("token_registered_by")
                if config.get("token_registration_time"):
                    self.token_registration_time = datetime.fromisoformat(config["token_registration_time"])
                self.monitored_players = config.get("monitored_players", {})
                self.chat_ids = config.get("chat_ids", {})
                print("[DEBUG] Конфигурация загружена")
            except Exception as e:
                print(f"[DEBUG] Ошибка при загрузке конфигурации: {e}")

    def register_tokens(self, match_token: str, auth_code: str, steam_api_key: str, user_id: int) -> str:
        print(f"[DEBUG] Регистрация токенов для пользователя {user_id}")
        self.match_token = match_token
        self.auth_code = auth_code
        self.steam_api_key = steam_api_key
        self.token_registered_by = user_id
        self.token_registration_time = datetime.now()
        self.save_config()  # Сохраняем конфигурацию после регистрации
        return "Токены успешно зарегистрированы!"

    def get_token_info(self) -> Optional[tuple[int, datetime]]:
        if self.token_registered_by:
            return self.token_registered_by, self.token_registration_time
        return None

    def get_player_status(self, steam_id: str) -> tuple[bool, str]:
        if not self.steam_api_key:
            print("[DEBUG] Ошибка: токены не зарегистрированы")
            return False, "Ошибка: токены не зарегистрированы!"
            
        url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.steam_api_key}&steamids={steam_id}"
        print(f"[DEBUG] Запрос статуса игрока {steam_id}")
        try:
            response = requests.get(url)
            print(f"[DEBUG] Ответ API: {response.status_code}")
            data = response.json()
            
            if data['response']['players']:
                player = data['response']['players'][0]
                game_id = player.get('gameid')
                player_name = player.get('personaname', steam_id)  # Получаем никнейм игрока
                print(f"[DEBUG] Игрок найден, game_id: {game_id}, имя: {player_name}")
                
                if game_id == '730':  # 730 - это ID для CS2
                    print(f"[DEBUG] Игрок {player_name} в CS2")
                    return True, f"Игрок {player_name} в данный момент играет в CS2"
                else:
                    print(f"[DEBUG] Игрок {player_name} не в CS2")
                    return False, f"Игрок {player_name} не в CS2"
            print(f"[DEBUG] Игрок {steam_id} не найден")
            return False, "Игрок не найден"
        except Exception as e:
            print(f"[DEBUG] Ошибка при получении статуса: {e}")
            return False, f"Ошибка при получении статуса: {str(e)}"

    def get_match_history(self, steam_id: str) -> dict:
        if not self.steam_api_key:
            return {"error": "Токены не зарегистрированы"}
            
        url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=730&key={self.steam_api_key}&steamid={steam_id}"
        try:
            response = requests.get(url)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def add_player_to_monitor(self, steam_id: str, chat_id: int) -> str:
        print(f"[DEBUG] Попытка добавить игрока {steam_id} для чата {chat_id}")
        if not self.steam_api_key:
            print("[DEBUG] Ошибка: токены не зарегистрированы при добавлении игрока")
            return "Ошибка: сначала необходимо зарегистрировать токены!"
            
        if steam_id in self.monitored_players:
            print(f"[DEBUG] Игрок {steam_id} уже отслеживается")
            return "Этот игрок уже отслеживается!"
        
        self.monitored_players[steam_id] = False
        self.chat_ids[steam_id] = chat_id
        self.save_config()  # Сохраняем конфигурацию после добавления игрока
        print(f"[DEBUG] Игрок {steam_id} успешно добавлен в отслеживание")
        return f"Игрок {steam_id} добавлен в отслеживание!"

    def remove_player_from_monitor(self, steam_id: str) -> str:
        if steam_id not in self.monitored_players:
            return "Этот игрок не отслеживается!"
        
        del self.monitored_players[steam_id]
        del self.chat_ids[steam_id]
        self.save_config()  # Сохраняем конфигурацию после удаления игрока
        return f"Игрок {steam_id} удален из отслеживания!"

    def check_players_status(self) -> list[tuple[int, str]]:
        if not self.steam_api_key:
            print("[DEBUG] Ошибка: токены не зарегистрированы при проверке статуса")
            if not self.chat_ids:
                return []
            first_chat_id = next(iter(self.chat_ids.values()))
            return [(first_chat_id, "Ошибка: токены не зарегистрированы!")]
            
        messages = []
        print(f"[DEBUG] Проверка статуса для игроков: {list(self.monitored_players.keys())}")
        
        for steam_id, was_in_game in self.monitored_players.items():
            print(f"[DEBUG] Проверка игрока {steam_id}, предыдущий статус: {'в игре' if was_in_game else 'не в игре'}")
            is_in_game, status = self.get_player_status(steam_id)
            chat_id = self.chat_ids[steam_id]
            
            # Получаем никнейм игрока
            url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.steam_api_key}&steamids={steam_id}"
            try:
                response = requests.get(url)
                data = response.json()
                player_name = data['response']['players'][0]['personaname'] if data['response']['players'] else steam_id
            except:
                player_name = steam_id
            
            if is_in_game and not was_in_game:
                print(f"[DEBUG] Игрок {player_name} зашел в CS2")
                messages.append((chat_id, f"🎮 Игрок {player_name} зашел в CS2!"))
                self.monitored_players[steam_id] = True
            elif not is_in_game and was_in_game:
                print(f"[DEBUG] Игрок {player_name} вышел из CS2")
                messages.append((chat_id, f"👋 Игрок {player_name} вышел из CS2!"))
                stats = self.get_match_history(steam_id)
                if 'playerstats' in stats:
                    stats_message = "📊 Статистика последнего матча:\n"
                    for stat in stats['playerstats']['stats']:
                        stats_message += f"{stat['name']}: {stat['value']}\n"
                    messages.append((chat_id, stats_message))
                self.monitored_players[steam_id] = False
        
        print(f"[DEBUG] Сгенерировано сообщений: {len(messages)}")
        return messages

    def get_monitored_players(self) -> list[str]:
        return list(self.monitored_players.keys())

def main():
    tracker = CS2PlayerTracker()
    tracker.register_tokens()
    
    steam_id = input("Введите Steam ID игрока для отслеживания: ")
    try:
        tracker.monitor_player(steam_id)
    except KeyboardInterrupt:
        print("\nМониторинг остановлен пользователем")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
