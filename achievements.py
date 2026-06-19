"""
Менеджер системы достижений (ачивок).
Хранит прогресс каждого игрока отдельно в файле achievements.json.
"""
import json
import os


class Achievement:
    """Представление одного достижения."""

    def __init__(self, ach_id: str, name: str, desc: str, icon: str, condition):
        self.id = ach_id
        self.name = name
        self.desc = desc
        self.icon = icon
        self.condition = condition  # lambda(stats) -> bool
        self.unlocked = False


class AchievementsManager:
    """
    Управляет достижениями для конкретного игрока.
    Данные хранятся в формате:
    {
        "players": {
            "PlayerName": {
                "unlocked": ["first_blood", ...],
                "stats": {"max_score": 0, ...}
            }
        }
    }
    """

    def __init__(self, player_name: str, save_path: str = "achievements.json"):
        self.save_path = save_path
        self.player_name = player_name
        self.achievements: dict[str, Achievement] = {}
        self.all_players_data: dict = {}
        self.unlocked_ids: list[str] = []
        self.stats: dict = self._default_stats()

        self._load()
        self._init_achievements()

        # Если игрока нет в базе — создаём запись
        if self.player_name not in self.all_players_data:
            self.all_players_data[self.player_name] = {
                "unlocked": [],
                "stats": self._default_stats(),
            }
            self._save()

        # Получаем данные текущего игрока
        self.player_data = self.all_players_data[self.player_name]
        self.unlocked_ids = list(self.player_data.get("unlocked", []))
        self.stats = dict(self.player_data.get("stats", self._default_stats()))

        # Применяем статус разблокировки к достижениям
        for ach in self.achievements.values():
            if ach.id in self.unlocked_ids:
                ach.unlocked = True

    @staticmethod
    def _default_stats() -> dict:
        """Структура статистики по умолчанию."""
        return {
            "max_score": 0,
            "max_length": 1,
            "total_bonuses": 0,
            "games_played": 0,
            "session_bonuses": 0,
        }

    def _init_achievements(self) -> None:
        """Инициализирует список доступных достижений."""
        defs = {
            "first_blood": (
                "first_blood",
                "Первая кровь",
                "Съешьте первый бонус",
                "",
                lambda s: s["total_bonuses"] >= 1,
            ),
            "speed_demon": (
                "speed_demon",
                "Демон скорости",
                "Наберите 30 очков за игру",
                "",
                lambda s: s["max_score"] >= 30,
            ),
            "marathon": (
                "marathon",
                "Марафонец",
                "Змейка вырастет до 30 сегментов",
                "",
                lambda s: s["max_length"] >= 30,
            ),
            "bonuses_hunter": (
                "bonuses_hunter",
                "Охотник за бонусами",
                "Съешьте 3 бонуса за одну игру",
                "",
                lambda s: s["session_bonuses"] >= 3,
            ),
            "veteran": (
                "veteran",
                "Ветеран",
                "Завершите 5 игр",
                "🎖️",
                lambda s: s["games_played"] >= 5,
            ),
        }
        for key, (aid, name, desc, icon, cond) in defs.items():
            self.achievements[key] = Achievement(aid, name, desc, icon, cond)

    def _load(self) -> None:
        """Загружает данные из файла. Если структура неверная — начинает с чистого листа."""
        if not os.path.exists(self.save_path):
            self.all_players_data = {}
            return

        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Принимаем только корректный формат с ключом "players"
            if isinstance(data, dict) and "players" in data:
                self.all_players_data = data["players"]
            else:
                # Устаревший или повреждённый формат — игнорируем
                print(f"⚠️ Файл {self.save_path} имеет устаревший формат. Начинаем с чистого листа.")
                self.all_players_data = {}
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️ Ошибка чтения {self.save_path}: {e}. Начинаем с чистого листа.")
            self.all_players_data = {}

    def _save(self) -> None:
        """Сохраняет данные текущего игрока в файл."""
        self.all_players_data[self.player_name] = {
            "unlocked": self.unlocked_ids,
            "stats": self.stats,
        }
        data = {"players": self.all_players_data}
        with open(self.save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_session_end(
        self, score: int, length: int, bonuses_eaten: int
    ) -> None:
        """Вызывается при Game Over для обновления статистики текущего игрока."""
        self.stats["max_score"] = max(self.stats["max_score"], score)
        self.stats["max_length"] = max(self.stats["max_length"], length)
        self.stats["total_bonuses"] += bonuses_eaten
        self.stats["session_bonuses"] = bonuses_eaten
        self.stats["games_played"] += 1
        self._save()

    def check_new_unlocks(self) -> list[Achievement]:
        """Проверяет условия и возвращает список только что открытых достижений."""
        new_unlocks = []
        for ach in self.achievements.values():
            if not ach.unlocked and ach.condition(self.stats):
                ach.unlocked = True
                if ach.id not in self.unlocked_ids:
                    self.unlocked_ids.append(ach.id)
                new_unlocks.append(ach)
        if new_unlocks:
            self._save()
        return new_unlocks

    def reset_session(self) -> None:
        """Сбрасывает статистику текущей сессии (вызывается при рестарте игры)."""
        self.stats["session_bonuses"] = 0

    def get_all_players(self) -> list[str]:
        """Возвращает список всех игроков (для возможного UI)."""
        return list(self.all_players_data.keys())