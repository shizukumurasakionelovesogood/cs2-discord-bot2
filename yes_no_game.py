import json
import os
from collections import defaultdict
import random

class YesNoGame:
    def __init__(self):
        self.questions = [
            # Игры
            {"question": "CS2 лучше Valorant?", "answer": "да", "category": "игры"},
            {"question": "Minecraft был создан в 2009 году?", "answer": "да", "category": "игры"},
            {"question": "GTA V продала более 100 миллионов копий?", "answer": "да", "category": "игры"},
            {"question": "The Witcher 3 получила более 800 наград?", "answer": "да", "category": "игры"},
            {"question": "Portal 2 длится менее 5 часов?", "answer": "нет", "category": "игры"},
            {"question": "Red Dead Redemption 2 вышел в 2018 году?", "answer": "да", "category": "игры"},
            {"question": "God of War (2018) доступен на Xbox?", "answer": "нет", "category": "игры"},
            {"question": "Dark Souls 3 сложнее первой части?", "answer": "да", "category": "игры"},
            {"question": "League of Legends старше Dota 2?", "answer": "да", "category": "игры"},
            {"question": "Cyberpunk 2077 вышел без багов?", "answer": "нет", "category": "игры"},

            # Математика
            {"question": "2 + 2 = 5?", "answer": "нет", "category": "математика"},
            {"question": "Пи (π) равно 3.14?", "answer": "нет", "category": "математика"},
            {"question": "Квадратный корень из 16 равен 4?", "answer": "да", "category": "математика"},
            {"question": "Сумма углов треугольника равна 180 градусам?", "answer": "да", "category": "математика"},
            {"question": "0.999... равно 1?", "answer": "да", "category": "математика"},
            {"question": "Число e (число Эйлера) меньше 3?", "answer": "нет", "category": "математика"},
            {"question": "Все простые числа нечетные?", "answer": "нет", "category": "математика"},
            {"question": "Квадрат имеет 5 сторон?", "answer": "нет", "category": "математика"},
            {"question": "1/3 в десятичной форме равна 0.333...?", "answer": "да", "category": "математика"},
            {"question": "Факториал 5 равен 120?", "answer": "да", "category": "математика"},

            # Физика
            {"question": "Вода закипает при 100 градусах Цельсия?", "answer": "да", "category": "физика"},
            {"question": "Свет распространяется быстрее звука?", "answer": "да", "category": "физика"},
            {"question": "Атом состоит только из протонов и электронов?", "answer": "нет", "category": "физика"},
            {"question": "Сила тяжести на Луне меньше, чем на Земле?", "answer": "да", "category": "физика"},
            {"question": "Все металлы проводят электричество?", "answer": "да", "category": "физика"},
            {"question": "Температура абсолютного нуля равна -273.15°C?", "answer": "да", "category": "физика"},
            {"question": "Скорость света постоянна во всех средах?", "answer": "нет", "category": "физика"},
            {"question": "Масса и вес - это одно и то же?", "answer": "нет", "category": "физика"},
            {"question": "Все газы при нагревании расширяются?", "answer": "да", "category": "физика"},
            {"question": "Энергия может быть создана из ничего?", "answer": "нет", "category": "физика"},

            # Химия
            {"question": "Вода состоит из водорода и кислорода?", "answer": "да", "category": "химия"},
            {"question": "Золото растворяется в воде?", "answer": "нет", "category": "химия"},
            {"question": "pH нейтральной воды равен 7?", "answer": "да", "category": "химия"},
            {"question": "Все кислоты опасны для человека?", "answer": "нет", "category": "химия"},
            {"question": "Углерод имеет 6 протонов?", "answer": "да", "category": "химия"},
            {"question": "Металлы могут быть жидкими при комнатной температуре?", "answer": "да", "category": "химия"},
            {"question": "Все органические вещества содержат углерод?", "answer": "да", "category": "химия"},
            {"question": "Кислород - это металл?", "answer": "нет", "category": "химия"},
            {"question": "Водород - самый легкий элемент?", "answer": "да", "category": "химия"},
            {"question": "Все соли растворяются в воде?", "answer": "нет", "category": "химия"},

            # Биология
            {"question": "Человек имеет 206 костей?", "answer": "да", "category": "биология"},
            {"question": "Все бактерии вредны для человека?", "answer": "нет", "category": "биология"},
            {"question": "ДНК содержит генетическую информацию?", "answer": "да", "category": "биология"},
            {"question": "Все растения фотосинтезируют?", "answer": "нет", "category": "биология"},
            {"question": "Человеческий мозг весит около 1.5 кг?", "answer": "да", "category": "биология"},
            {"question": "Все млекопитающие живородящие?", "answer": "нет", "category": "биология"},
            {"question": "Кровь человека всегда красная?", "answer": "да", "category": "биология"},
            {"question": "Все вирусы вызывают болезни?", "answer": "нет", "category": "биология"},
            {"question": "Человек имеет 5 чувств?", "answer": "нет", "category": "биология"},
            {"question": "Все грибы являются растениями?", "answer": "нет", "category": "биология"},

            # История
            {"question": "Вторая мировая война началась в 1939 году?", "answer": "да", "category": "история"},
            {"question": "Наполеон был ростом выше 180 см?", "answer": "нет", "category": "история"},
            {"question": "Римская империя пала в 476 году?", "answer": "да", "category": "история"},
            {"question": "Колумб открыл Америку в 1492 году?", "answer": "да", "category": "история"},
            {"question": "Все египетские пирамиды были построены рабами?", "answer": "нет", "category": "история"},
            {"question": "Первая мировая война длилась 4 года?", "answer": "да", "category": "история"},
            {"question": "Древние греки изобрели демократию?", "answer": "да", "category": "история"},
            {"question": "Все римские императоры были мужчинами?", "answer": "нет", "category": "история"},
            {"question": "Великая китайская стена видна из космоса?", "answer": "нет", "category": "история"},
            {"question": "Древние египтяне поклонялись только одному богу?", "answer": "нет", "category": "история"},

            # География
            {"question": "Земля плоская?", "answer": "нет", "category": "география"},
            {"question": "Антарктида - самый холодный континент?", "answer": "да", "category": "география"},
            {"question": "Все страны имеют выход к морю?", "answer": "нет", "category": "география"},
            {"question": "Сахара - самая большая пустыня в мире?", "answer": "да", "category": "география"},
            {"question": "Амазонка - самая длинная река в мире?", "answer": "нет", "category": "география"},
            {"question": "Все страны в Европе являются членами ЕС?", "answer": "нет", "category": "география"},
            {"question": "Мертвое море - самое соленое озеро в мире?", "answer": "да", "category": "география"},
            {"question": "Все острова окружены водой?", "answer": "да", "category": "география"},
            {"question": "Эверест - самая высокая гора в мире?", "answer": "да", "category": "география"},
            {"question": "Все страны в Африке бедные?", "answer": "нет", "category": "география"},

            # Астрономия
            {"question": "Солнце вращается вокруг Земли?", "answer": "нет", "category": "астрономия"},
            {"question": "Марс имеет два спутника?", "answer": "да", "category": "астрономия"},
            {"question": "Все планеты солнечной системы имеют кольца?", "answer": "нет", "category": "астрономия"},
            {"question": "Плутон все еще считается планетой?", "answer": "нет", "category": "астрономия"},
            {"question": "Венера ближе к Солнцу, чем Меркурий?", "answer": "нет", "category": "астрономия"},
            {"question": "Все звезды белого цвета?", "answer": "нет", "category": "астрономия"},
            {"question": "Луна всегда показывает одну сторону Земле?", "answer": "да", "category": "астрономия"},
            {"question": "Все кометы имеют хвост?", "answer": "да", "category": "астрономия"},
            {"question": "Юпитер - самая большая планета солнечной системы?", "answer": "да", "category": "астрономия"},
            {"question": "Все метеориты падают на Землю?", "answer": "нет", "category": "астрономия"},

            # Программирование
            {"question": "Python был создан в 1991 году?", "answer": "да", "category": "программирование"},
            {"question": "JavaScript и Java - это один и тот же язык?", "answer": "нет", "category": "программирование"},
            {"question": "Все программы можно написать на любом языке программирования?", "answer": "да", "category": "программирование"},
            {"question": "HTML - это язык программирования?", "answer": "нет", "category": "программирование"},
            {"question": "Git был создан Линусом Торвальдсом?", "answer": "да", "category": "программирование"},
            {"question": "Все базы данных используют SQL?", "answer": "нет", "category": "программирование"},
            {"question": "Linux - это операционная система?", "answer": "да", "category": "программирование"},
            {"question": "Все программы с открытым исходным кодом бесплатны?", "answer": "нет", "category": "программирование"},
            {"question": "Python медленнее C++?", "answer": "да", "category": "программирование"},
            {"question": "Все веб-сайты используют JavaScript?", "answer": "нет", "category": "программирование"},

            # Общие знания
            {"question": "В неделе 8 дней?", "answer": "нет", "category": "общие знания"},
            {"question": "В году 365 дней?", "answer": "да", "category": "общие знания"},
            {"question": "Все птицы умеют летать?", "answer": "нет", "category": "общие знания"},
            {"question": "Человек может прожить без воды 3 дня?", "answer": "да", "category": "общие знания"},
            {"question": "Все рыбы живут в воде?", "answer": "нет", "category": "общие знания"},
            {"question": "Человек использует только 10% мозга?", "answer": "нет", "category": "общие знания"},
            {"question": "Все змеи ядовиты?", "answer": "нет", "category": "общие знания"},
            {"question": "Человек может прожить без сна 11 дней?", "answer": "да", "category": "общие знания"},
            {"question": "Все млекопитающие теплокровные?", "answer": "да", "category": "общие знания"},
            {"question": "Человек может прожить без еды 30 дней?", "answer": "да", "category": "общие знания"}
        ]
        self.player_stats = defaultdict(lambda: {
            "correct": 0, 
            "total": 0, 
            "points": 0,
            "category_stats": defaultdict(lambda: {"correct": 0, "total": 0, "points": 0})
        })
        self.load_stats()

    def load_stats(self):
        if os.path.exists('yes_no_stats.json'):
            with open('yes_no_stats.json', 'r', encoding='utf-8') as f:
                self.player_stats = defaultdict(lambda: {
                    "correct": 0, 
                    "total": 0, 
                    "points": 0,
                    "category_stats": defaultdict(lambda: {"correct": 0, "total": 0, "points": 0})
                }, json.load(f))

    def save_stats(self):
        with open('yes_no_stats.json', 'w', encoding='utf-8') as f:
            json.dump(dict(self.player_stats), f, ensure_ascii=False, indent=4)

    def get_random_question(self):
        return random.choice(self.questions)

    def check_answer(self, question, answer, player_id):
        correct = answer.lower() == question["answer"].lower()
        self.player_stats[player_id]["total"] += 1
        
        if correct:
            self.player_stats[player_id]["correct"] += 1
            points = 10  # Базовые очки за правильный ответ
            self.player_stats[player_id]["points"] += points
            self.player_stats[player_id]["category_stats"][question["category"]]["correct"] += 1
            self.player_stats[player_id]["category_stats"][question["category"]]["points"] += points
            
        self.player_stats[player_id]["category_stats"][question["category"]]["total"] += 1
        self.save_stats()
        return correct

    def get_player_stats(self, player_id):
        if player_id not in self.player_stats:
            return "У вас пока нет статистики. Сыграйте несколько игр!"
        
        stats = self.player_stats[player_id]
        total = stats["total"]
        correct = stats["correct"]
        points = stats["points"]
        accuracy = (correct / total * 100) if total > 0 else 0

        response = f"📊 Ваша статистика (сохраняется между сессиями):\n"
        response += f"Всего вопросов: {total}\n"
        response += f"Правильных ответов: {correct}\n"
        response += f"Точность: {accuracy:.1f}%\n"
        response += f"🏆 Очки: {points}\n\n"
        response += "📈 Статистика по категориям:\n"

        for category, cat_stats in stats["category_stats"].items():
            cat_accuracy = (cat_stats["correct"] / cat_stats["total"] * 100) if cat_stats["total"] > 0 else 0
            response += f"{category}: {cat_stats['correct']}/{cat_stats['total']} ({cat_accuracy:.1f}%) - {cat_stats['points']} очков\n"

        return response

    def get_top_players(self, limit=3):
        players = []
        for player_id, stats in self.player_stats.items():
            if stats["total"] >= 5:  # Минимум 5 вопросов для попадания в топ
                accuracy = (stats["correct"] / stats["total"] * 100)
                players.append({
                    "id": player_id,
                    "accuracy": accuracy,
                    "total": stats["total"],
                    "correct": stats["correct"],
                    "points": stats["points"]
                })
        
        # Сортируем по очкам, точности и количеству правильных ответов
        players.sort(key=lambda x: (x["points"], x["accuracy"], x["correct"]), reverse=True)
        return players[:limit] 