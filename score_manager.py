import json
import os

class ScoreManager:
    def __init__(self, filename="scores.json"):
        self.filename = filename
        self.scores = {}
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.scores = json.load(f)
            except json.JSONDecodeError:
                self.scores = {}

    def update_score(self, name, score):
        if name not in self.scores or score > self.scores[name]:
            self.scores[name] = score
            self._save()

    def get_leaderboard(self, limit=5):
        """
        Возвращает отсортированный список лучших игроков.

        :param limit: Количество записей в топе (int)
        :return: Список кортежей [(имя, счёт), ...]
        """
        sorted_scores = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_scores[:limit]

    def get_best_score(self, name):
        return self.scores.get(name, 0)

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.scores, f, indent=2, ensure_ascii=False)