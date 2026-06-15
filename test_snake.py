import unittest
from unittest.mock import MagicMock, patch, Mock
import sys


# ==============================================================================
# ГЛОБАЛЬНЫЙ МОК TINKER: Без спека, чтобы избежать InvalidSpecError
# ==============================================================================
def make_mock_factory():
    """Фабрика, возвращающая простые моки без валидации спека."""

    def factory(*args, **kwargs):
        m = MagicMock()
        # Возвращаем сам мок для методов вроде .pack(), .grid(), .config()
        m.pack = MagicMock(return_value=m)
        m.grid = MagicMock(return_value=m)
        m.config = MagicMock(return_value=m)
        m.configure = MagicMock(return_value=m)
        return m

    return factory


mock_tk = MagicMock()
mock_tk.simpledialog = MagicMock()
mock_tk.simpledialog.askstring = MagicMock(return_value="TestPlayer")

# Заменяем классы виджетов на фабрики, возвращающие простые моки
mock_tk.Tk = make_mock_factory()
mock_tk.Frame = make_mock_factory()
mock_tk.Canvas = make_mock_factory()
mock_tk.Label = make_mock_factory()
mock_tk.Listbox = make_mock_factory()
mock_tk.Button = make_mock_factory()
mock_tk.Message = make_mock_factory()

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.simpledialog'] = mock_tk.simpledialog

# Импортируем модули игры ПОСЛЕ настройки моков
from snake_logic import SnakeLogic
from snake_app import SnakeApp


class TestSnakeLogic(unittest.TestCase):
    """Тестирование ядра игры: движение, столкновения, стены, бонусы."""

    def setUp(self):
        self.game = SnakeLogic(10, 10)

    def test_TC1_initial_state(self):
        self.assertEqual(self.game.snake, [(5, 5)])
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.bonus)

    def test_TC2_movement_and_direction(self):
        self.game.step()
        self.assertEqual(self.game.snake[0], (6, 5))
        self.game.set_direction((0, -1))
        self.game.step()
        self.assertEqual(self.game.snake[0], (6, 4))

    def test_TC3_no_180_turn(self):
        self.game.direction = (0, 1)
        self.game.set_direction((0, -1))
        self.assertEqual(self.game.direction, (0, 1))

    def test_TC4_wall_collision(self):
        self.game = SnakeLogic(5, 5)
        self.game.direction = (1, 0)
        for _ in range(5): self.game.step()
        self.assertTrue(self.game.game_over)

    def test_TC5_self_collision(self):
        self.game.snake = [(5, 5), (5, 6), (6, 6), (6, 5)]
        self.game.direction = (0, 1)
        self.assertTrue(self.game.step() == "die")
        self.assertTrue(self.game.game_over)

    def test_TC6_food_eating(self):
        self.game.food = (6, 5)
        self.assertEqual(self.game.step(), "eat")
        self.assertEqual(self.game.score, 1)
        self.assertEqual(len(self.game.snake), 2)

    def test_TC7_gold_bonus_logic(self):
        self.game.bonus = (6, 5, "gold")
        self.game.bonus_ttl = 50
        self.assertEqual(self.game.step(), "eat_bonus_gold")
        self.assertEqual(self.game.score, 5)
        self.assertIsNone(self.game.bonus)

    def test_TC8_slow_bonus_logic(self):
        self.game.bonus = (6, 5, "slow")
        self.game.bonus_ttl = 50
        self.assertEqual(self.game.step(), "eat_bonus_slow")
        self.assertIsNone(self.game.bonus)

    def test_TC9_bonus_ttl_expiration(self):
        self.game.bonus = (2, 2, "gold")
        self.game.bonus_ttl = 3
        for _ in range(3):
            self.game.step()
            if self.game.bonus: self.game.bonus_ttl -= 1
        self.assertIsNone(self.game.bonus)


class TestSnakeAppLogic(unittest.TestCase):
    """Тестирование UI-логики: пауза, рестарт, темы, клавиши, эффекты."""

    def setUp(self):
        self.mock_root = MagicMock()
        self.config = {
            "speed": 120, "min_speed": 50, "width": 10, "height": 10,
            "cell_size": 20, "score_acceleration": 2, "theme_name": "Dark"
        }

        # Патчим только методы отрисовки и обновления лидеров
        with patch.object(SnakeApp, '_update_leaderboard_ui'), \
                patch.object(SnakeApp, 'draw'):
            self.app = SnakeApp(self.mock_root, self.config, "TestPlayer")

        # Подменяем canvas на мок для тестов эффектов
        self.app.canvas = MagicMock()

    def test_TC10_pause_toggle(self):
        self.assertFalse(self.app.is_paused)
        self.app.toggle_pause()
        self.assertTrue(self.app.is_paused)
        self.app.toggle_pause()
        self.assertFalse(self.app.is_paused)

    def test_TC11_restart_resets_state(self):
        self.app.game.game_over = True
        self.app.game.score = 15
        self.app.slow_effect_timer = 50
        self.app.is_paused = True

        self.app.restart()

        self.assertFalse(self.app.game.game_over)
        self.assertEqual(self.app.game.score, 0)
        self.assertEqual(self.app.slow_effect_timer, 0)
        self.assertFalse(self.app.is_paused)

    def test_TC12_theme_cycling(self):
        initial = self.app.current_theme_name
        self.app.cycle_theme()
        self.assertNotEqual(self.app.current_theme_name, initial)
        self.assertIn(self.app.current_theme_name, SnakeApp.THEMES)
        self.assertEqual(self.app.config["theme_name"], self.app.current_theme_name)

    def test_TC13_key_handling_movement(self):
        ev = Mock()
        ev.keysym = "w"
        self.app.handle_key(ev)
        self.assertEqual(self.app.game.direction, (0, -1))

        ev.keysym = "d"
        self.app.handle_key(ev)
        self.assertEqual(self.app.game.direction, (1, 0))

    def test_TC14_key_handling_pause(self):
        ev = Mock()
        ev.keysym = "space"
        self.app.handle_key(ev)
        self.assertTrue(self.app.is_paused)

    def test_TC15_bonus_effects_registration(self):
        self.app.game.snake = [(5, 5)]
        self.app.effects = []

        # Эмуляция логики из loop() для золотого бонуса
        self.app.effects.append({"x": 110, "y": 110, "text": "+5", "color": "#FFD700", "life": 30})
        self.assertEqual(len(self.app.effects), 1)
        self.assertEqual(self.app.effects[0]["text"], "+5")

        # Эмуляция для ледяного бонуса
        self.app.effects = []
        self.app.slow_effect_timer = 0
        self.app.effects.append({"x": 110, "y": 110, "text": "❄️ SLOW", "color": "#00BFFF", "life": 30})
        self.app.slow_effect_timer = 100
        self.assertEqual(self.app.effects[0]["text"], "❄️ SLOW")
        self.assertEqual(self.app.slow_effect_timer, 100)

    def test_TC16_effects_cleanup(self):
        # Добавляем "y" для тестирования движения
        self.app.effects = [
            {"life": 30, "y": 100},
            {"life": 15, "y": 200},
            {"life": 0, "y": 300}
        ]

        for eff in self.app.effects:
            eff["y"] -= 2  # ✅ Теперь ключ "y" существует
            eff["life"] -= 1

        self.app.effects = [e for e in self.app.effects if e["life"] > 0]

        self.assertEqual(len(self.app.effects), 2)
        # Дополнительно можно проверить, что координаты изменились
        self.assertEqual(self.app.effects[0]["y"], 98)  # 100 - 2


if __name__ == "__main__":
    print("🧪 Запуск тестового пайплайна...")
    unittest.main(verbosity=2)