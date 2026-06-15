import json
import os

class Achievement:
    def __init__(self, ach_id, name, desc, icon, condition):
        self.id = ach_id
        self.name = name
        self.desc = desc
        self.icon = icon
        self.condition = condition  # lambda, принимающая dict stats
        self.unlocked = False

class AchievementsManager:
    def __init__(self, save_path="achievements.json"):
        self.save_path = save_path
        self.achievements = {}
        # Глобальная статистика игрока
        self.stats = {
            "max_score": 0,
            "max_length": 1,
            "total_bonuses": 0,
            "games_played": 0,
            "session_bonuses": 0  # Сбрасывается каждую игру
        }
        self.unlocked_ids = []
        self._load()
        self._init_achievements()

    def _init_achievements(self):
        # Формат: ключ: (id, имя, описание, иконка, условие)
        defs = {
            "first_blood": ("first_blood", "Первая кровь", "Съешьте первый бонус", "", lambda s: s["total_bonuses"] >= 1),
            "speed_demon": ("speed_demon", "Демон скорости", "Наберите 30 очков за игру", "", lambda s: s["max_score"] >= 30),
            "marathon": ("marathon", "Марафонец", "Змейка вырастет до 30 сегментов", "", lambda s: s["max_length"] >= 30),
            "bonuses_hunter": ("bonuses_hunter", "Охотник за бонусами", "Съешьте 3 бонуса за одну игру", "", lambda s: s["session_bonuses"] >= 3),
            "veteran": ("veteran", "Ветеран", "Завершите 5 игр", "🎖️", lambda s: s["games_played"] >= 5)
        }
        for key, (aid, name, desc, icon, cond) in defs.items():
            self.achievements[key] = Achievement(aid, name, desc, icon, cond)
            if aid in self.unlocked_ids:
                self.achievements[key].unlocked = True

    def _load(self):
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.unlocked_ids = data.get("unlocked", [])
                    self.stats.update(data.get("stats", {}))
            except Exception:
                pass

    def _save(self):
        data = {"unlocked": self.unlocked_ids, "stats": self.stats}
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_session_end(self, score, length, bonuses_eaten):
        """Вызывается при Game Over для обновления статистики."""
        self.stats["max_score"] = max(self.stats["max_score"], score)
        self.stats["max_length"] = max(self.stats["max_length"], length)
        self.stats["total_bonuses"] += bonuses_eaten
        self.stats["session_bonuses"] = bonuses_eaten
        self.stats["games_played"] += 1
        self._save()

    def check_new_unlocks(self):
        """Проверяет условия и возвращает список только что открытых достижений."""
        new_unlocks = []
        for ach in self.achievements.values():
            if not ach.unlocked and ach.condition(self.stats):
                ach.unlocked = True
                self.unlocked_ids.append(ach.id)
                new_unlocks.append(ach)
        if new_unlocks:
            self._save()
        return new_unlocks

    def reset_session(self):
        self.stats["session_bonuses"] = 0