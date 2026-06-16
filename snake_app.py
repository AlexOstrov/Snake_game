import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os
import time
import argparse
from PIL import Image, ImageTk
from snake_logic import SnakeLogic
from sound_manager import SoundManager
from score_manager import ScoreManager
from achievements import AchievementsManager


class FloatingText:
    """Класс для создания всплывающего текста (эффект +5, SLOW и т.д.)."""

    def __init__(self, canvas, x, y, text, color="yellow"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.life = 35
        self.id = self.canvas.create_text(x, y, text=text, fill=color, font=("Arial", 16, "bold"))
        self.animate()

    def animate(self):
        self.y -= 2
        self.canvas.coords(self.id, self.x, self.y)
        self.life -= 1
        if self.life > 0:
            self.canvas.winfo_toplevel().after(50, self.animate)
        else:
            self.canvas.delete(self.id)


class SnakeApp:
    # --- Конфигурация Тем (Очищена от пробелов) ---
    THEMES = {
        "Dark": {"bg": "#1e1e1e", "snake_head": "#00ff00", "snake_body": "#00cc00", "food": "#ff3333",
                 "text": "#ffffff", "grid": "#333333", "pause_text": "#ffffff", "wall": "#555555",
                 "bonus_gold": "#ffd700", "bonus_slow": "#00bfff"},
        "Light": {"bg": "#f0f0f0", "snake_head": "#333333", "snake_body": "#666666", "food": "#e91e63",
                  "text": "#000000", "grid": "#cccccc", "pause_text": "#000000", "wall": "#888888",
                  "bonus_gold": "#ffaa00", "bonus_slow": "#0077ff"},
        "Matrix": {"bg": "#000000", "snake_head": "#00ff00", "snake_body": "#008800", "food": "#00ff00",
                   "text": "#00ff00", "grid": "#003300", "pause_text": "#00ff00", "wall": "#004400",
                   "bonus_gold": "#ffd700", "bonus_slow": "#00ffff"},
        "Ice": {"bg": "#e0f7fa", "snake_head": "#006064", "snake_body": "#00838f", "food": "#ff6f00",
                "text": "#006064", "grid": "#b2ebf2", "pause_text": "#006064", "wall": "#81d4fa",
                "bonus_gold": "#ff6f00", "bonus_slow": "#00bfff"}
    }

    def __init__(self, root, config, player_name):
        # 1. Инициализация root ДО использования
        self.root = root
        self.config = config
        self.player_name = player_name
        self.initial_speed = config["speed"]
        self.min_speed = config.get("min_speed", 50)
        self.acceleration_step = config.get("score_acceleration", 2)
        self.current_theme_name = config.get("theme_name", "Dark")

        if self.current_theme_name not in self.THEMES:
            self.current_theme_name = "Dark"

        # 2. Логика игры
        self.game = SnakeLogic(config["width"], config["height"])
        self.cell_size = config["cell_size"]

        # 3. Графика (Спрайты)
        self.snake_sprites = {}
        self._load_snake_sprites()
        self._load_wall_sprite()
        self._load_bonus_sprites()
        self._load_food_sprite()  # ✅ Загружаем спрайт еды
        self._sprite_refs = [self.snake_sprites, getattr(self, 'wall_sprite', None),
                             getattr(self, 'bonus_gold_sprite', None),
                             getattr(self, 'bonus_slow_sprite', None),
                             getattr(self, 'bonus_magnet_sprite', None),  # ✅ Добавили
                             getattr(self, 'food_sprite', None)]

        # 4. Менеджеры
        self.sound = SoundManager()
        self.scores = ScoreManager()
        self.achievements = AchievementsManager()

        # 5. Состояние
        self.is_paused = False
        self.session_bonuses = 0
        self.toast_label = None
        self.effects = []
        self.slow_effect_timer = 0
        self.magnet_effect_timer = 0  # ✅ Таймер эффекта магнита

        # 6. Анимация движения
        self.prev_positions = [(x, y) for x, y in self.game.snake]
        self.curr_positions = list(self.prev_positions)
        self.snake_items = []  # Список ID объектов Canvas для змейки
        self.move_progress = 0.0
        self._last_time = time.perf_counter()
        self._pending_direction = None

        # 7. Применение темы и создание UI
        self._apply_theme_colors()
        self.root.title(f"Змейка | Игрок: {player_name}")
        self.root.resizable(False, False)

        self.main_frame = tk.Frame(root, bg=self.theme["bg"])
        self.main_frame.pack(padx=10, pady=10)

        self.width_px = self.game.width * self.cell_size
        self.height_px = self.game.height * self.cell_size
        self.canvas = tk.Canvas(self.main_frame, width=self.width_px, height=self.height_px,
                                bg=self.theme["bg"], highlightthickness=1, highlightbackground=self.theme["grid"])
        self.canvas.grid(row=0, column=0, rowspan=2)

        # ✅ ИНИЦИАЛИЗАЦИЯ СТАТИЧЕСКИХ ОБЪЕКТОВ
        self._draw_walls()  # Рисуем стены ОДИН РАЗ
        self._init_snake_canvas_items()  # Создаем сегменты змейки ОДИН РАЗ

        # UI Лидеры
        self.leaderboard_frame = tk.Frame(self.main_frame, bg=self.theme["bg"], width=150, height=self.height_px)
        self.leaderboard_frame.grid(row=0, column=1, rowspan=2, padx=10, sticky="ns")
        self.leaderboard_frame.grid_propagate(False)

        tk.Label(self.leaderboard_frame, text="🏆 Лидеры", fg=self.theme["text"], bg=self.theme["bg"],
                 font=("Arial", 12, "bold")).pack(pady=(10, 5))

        self.lb_listbox = tk.Listbox(self.leaderboard_frame, bg=self.theme["bg"], fg=self.theme["text"],
                                     font=("Courier", 10), borderwidth=0, highlightthickness=0)
        self.lb_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._update_leaderboard_ui()

        # UI Кнопки
        self.controls_frame = tk.Frame(self.main_frame, bg=self.theme["bg"])
        self.controls_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        self.btn_theme = tk.Button(self.controls_frame, text="🎨 Тема (T)", command=self.cycle_theme,
                                   bg=self.theme.get("snake_body", "#ccc"), fg=self.theme.get("bg", "#000"))
        self.btn_theme.pack(side=tk.LEFT, padx=5)

        self.btn_ach = tk.Button(self.controls_frame, text="🏆 Ачивки (A)", command=self.show_achievements,
                                 bg=self.theme.get("snake_body", "#ccc"), fg=self.theme.get("bg", "#000"))
        self.btn_ach.pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(self.main_frame, text="", fg=self.theme["text"], bg=self.theme["bg"],
                                   font=("Arial", 12))
        self.info_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

        self.current_delay = self.initial_speed
        self._loop_id = None
        self.root.bind("<Key>", self.handle_key)
        # ✅ Активация тестового бонуса (если указан через --event)
        self.test_event = None  # Будет установлен извне
        self._activate_test_event()

        # Запуск цикла
        self.loop()

    # ==================== МЕТОДЫ ЗАГРУЗКИ ГРАФИКИ ====================

    def _load_snake_sprites(self):
        parts = ["head", "body", "tail"]
        directions = ["up", "down", "left", "right"]
        size = (self.cell_size, self.cell_size)
        try:
            for part in parts:
                for direction in directions:
                    filename = f"assets/{part}_{direction}.png"
                    if os.path.exists(filename):
                        img = Image.open(filename).resize(size, Image.Resampling.LANCZOS).convert("RGBA")
                        self.snake_sprites[(direction, part)] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Ошибка загрузки графики змейки: {e}")

    def _load_wall_sprite(self):
        try:
            if self.current_theme_name in ["Dark", "Light"]:
                wall_file = "assets/wall_brick.png"
            elif self.current_theme_name == "Ice":
                wall_file = "assets/wall_stone.png"
            elif self.current_theme_name == "Matrix":
                wall_file = "assets/wall_neon.png"
            else:
                wall_file = "assets/wall_brick.png"

            if os.path.exists(wall_file):
                wall_img = Image.open(wall_file).resize((self.cell_size, self.cell_size),
                                                        Image.Resampling.LANCZOS).convert("RGBA")
                self.wall_sprite = ImageTk.PhotoImage(wall_img)
            else:
                self.wall_sprite = None
        except Exception:
            self.wall_sprite = None

    def _load_bonus_sprites(self):
        try:
            size = (self.cell_size, self.cell_size)
            if os.path.exists("assets/bonus_gold.png"):
                self.bonus_gold_sprite = ImageTk.PhotoImage(
                    Image.open("assets/bonus_gold.png").resize(size, Image.Resampling.LANCZOS).convert("RGBA"))
            else:
                self.bonus_gold_sprite = None
            if os.path.exists("assets/bonus_slow.png"):
                self.bonus_slow_sprite = ImageTk.PhotoImage(
                    Image.open("assets/bonus_slow.png").resize(size, Image.Resampling.LANCZOS).convert("RGBA"))
            else:
                self.bonus_slow_sprite = None
            # ✅ Загрузка спрайта магнита
            if os.path.exists("assets/bonus_magnit.png"):
                self.bonus_magnet_sprite = ImageTk.PhotoImage(
                    Image.open("assets/bonus_magnit.png").resize(size, Image.Resampling.LANCZOS).convert("RGBA"))
            else:
                self.bonus_magnet_sprite = None

        except Exception:
            self.bonus_gold_sprite = None
            self.bonus_slow_sprite = None
            self.bonus_magnet_sprite = None

    def _load_food_sprite(self):
        """Загружает спрайт еды (красное яблоко)."""
        try:
            size = (self.cell_size, self.cell_size)
            food_path = "assets/food_apple.png"
            if os.path.exists(food_path):
                food_img = Image.open(food_path).resize(size, Image.Resampling.LANCZOS).convert("RGBA")
                self.food_sprite = ImageTk.PhotoImage(food_img)
                # Добавляем в защиту от сборщика мусора
                if not hasattr(self, '_sprite_refs'): self._sprite_refs = []
                self._sprite_refs.append(self.food_sprite)
            else:
                self.food_sprite = None
        except Exception as e:
            print(f"Ошибка загрузки спрайта еды: {e}")
            self.food_sprite = None

    # ==================== МЕТОДЫ ОТРИСОВКИ (ОПТИМИЗИРОВАННО) ====================

    def _draw_walls(self):
        """Рисует стены один раз. Вызывается при старте, рестарте или смене темы."""
        self.canvas.delete("walls")  # Удаляем старые стены (только при необходимости)
        for x, y in self.game.walls:
            px, py = x * self.cell_size, y * self.cell_size
            if hasattr(self, 'wall_sprite') and self.wall_sprite:
                self.canvas.create_image(px, py, image=self.wall_sprite, anchor=tk.NW, tags="walls")
            else:
                self.canvas.create_rectangle(px, py, px + self.cell_size, py + self.cell_size,
                                             fill=self.theme.get("wall", "#555"), outline="#000", tags="walls")

    def _init_snake_canvas_items(self):
        """Создает Canvas-элементы для змейки один раз (тег 'snake')."""
        self.snake_items = []
        for i, (x, y) in enumerate(self.game.snake):
            # При инициализации создаем любой спрайт (например, head_right),
            # метод render() мгновенно заменит его на правильный в первом кадре.
            px, py = x * self.cell_size, y * self.cell_size

            # Пробуем загрузить спрайт, иначе создаем прямоугольник
            sprite = self.snake_sprites.get(("right", "head" if i == 0 else "body"))

            if sprite:
                item = self.canvas.create_image(px, py, image=sprite, anchor=tk.NW, tags="snake")
            else:
                color = self.theme["snake_head"] if i == 0 else self.theme["snake_body"]
                item = self.canvas.create_rectangle(px, py, px + self.cell_size, py + self.cell_size,
                                                    fill=color, outline=self.theme["bg"], width=1, tags="snake")
            self.snake_items.append(item)

    def render(self):
        """Основной метод отрисовки. Обновляет ТОЛЬКО динамические объекты."""
        # ✅ УДАЛЯЕМ ТОЛЬКО ДИНАМИКУ (еда, бонусы, эффекты, пауза).
        self.canvas.delete("dynamic")

        # 🧲 ЭФФЕКТ МАГНИТА: Притягиваем еду к змейке
        if self.magnet_effect_timer > 0:
            head_x, head_y = self.game.snake[0]
            food_x, food_y = self.game.food

            # Проверяем расстояние (в клетках)
            distance = abs(head_x - food_x) + abs(head_y - food_y)

            # Если еда в радиусе 3 клеток - притягиваем
            if 0 < distance <= 3:
                # Двигаем еду к голове
                if food_x < head_x:
                    food_x += 1
                elif food_x > head_x:
                    food_x -= 1
                if food_y < head_y:
                    food_y += 1
                elif food_y > head_y:
                    food_y -= 1

                # ✅ Если еда достигла головы - съедаем её
                if food_x == head_x and food_y == head_y:
                    # Эмулируем съедание еды
                    self.game.score += 1
                    self.game.food = self.game._spawn_food()
                    self.sound.play("eat")

                    # Добавляем визуальный эффект
                    self.effects.append({
                        "x": head_x * self.cell_size + self.cell_size / 2,
                        "y": head_y * self.cell_size + self.cell_size / 2,
                        "text": "🧲 +1",
                        "color": "#FF1493",
                        "life": 25
                    })
                else:
                    # Просто двигаем еду
                    self.game.food = (food_x, food_y)

        # 1. Еда (Спрайт или Fallback)
        fx, fy = self.game.food
        px, py = fx * self.cell_size, fy * self.cell_size

        if hasattr(self, 'food_sprite') and self.food_sprite:
            # ✅ Рисуем красивое яблоко
            self.canvas.create_image(px, py, image=self.food_sprite, anchor=tk.NW, tags="dynamic")
        else:
            # Fallback: старый овал, если картинка не найдена
            self.canvas.create_oval(px, py, px + self.cell_size, py + self.cell_size,
                                    fill=self.theme["food"], tags="dynamic")

        # 2. Бонусы
        if self.game.bonus:
            bx, by, b_type = self.game.bonus

            # ✅ Проверяем, нужно ли скрыть бонус (эффект мигания перед исчезновением)
            is_blinking = self.game.bonus_ttl < 15 and (self.game.bonus_ttl // 3) % 2 == 0

            # Рисуем бонус ТОЛЬКО если он не в "слепой" фазе мигания
            if not is_blinking:
                px, py = bx * self.cell_size, by * self.cell_size
                color = self.theme.get("bonus_gold") if b_type == "gold" else \
                    self.theme.get("bonus_slow") if b_type == "slow" else \
                        self.theme.get("bonus_magnet", "#FF1493")

                sprite = self.bonus_gold_sprite if b_type == "gold" else \
                    self.bonus_slow_sprite if b_type == "slow" else \
                        self.bonus_magnet_sprite

                if sprite:
                    self.canvas.create_image(px, py, image=sprite, anchor=tk.NW, tags="dynamic")
                else:
                    # Fallback: овал, если спрайт не найден
                    self.canvas.create_oval(px + 2, py + 2, px + self.cell_size - 2, py + self.cell_size - 2,
                                            fill=color, outline="white", width=2, tags="dynamic")

        # 3. Змейка (Интерполяция + ДИНАМИЧЕСКАЯ СМЕНА СПРАЙТОВ)
        # Это исправляет ВСЕ 3 ошибки: направление головы, направление хвоста и превращение хвоста в тело
        snake_len = len(self.snake_items)

        for i, item_id in enumerate(self.snake_items):
            if i < len(self.prev_positions) and i < len(self.curr_positions):
                # --- А. Вычисляем координаты (Плавное движение) ---
                px_prev, py_prev = self.prev_positions[i]
                px_curr, py_curr = self.curr_positions[i]
                interp_x = px_prev + (px_curr - px_prev) * self.move_progress
                interp_y = py_prev + (py_curr - py_prev) * self.move_progress

                # Двигаем объект (2 координаты для изображения)
                self.canvas.coords(item_id, interp_x * self.cell_size, interp_y * self.cell_size)

                # --- Б. Вычисляем направление и тип части (Голова/Тело/Хвост) ---
                part_type = "body"
                dx, dy = 0, 0

                if i == 0:
                    part_type = "head"
                    # Голова смотрит туда, куда движется игра
                    dx, dy = self.game.direction
                else:
                    # Тело и Хвост смотрят на предыдущий сегмент (i-1)
                    # Используем дискретные координаты игры для точного определения вектора
                    if i < len(self.game.snake):
                        prev_seg = self.game.snake[i - 1]
                        curr_seg = self.game.snake[i]
                        dx = prev_seg[0] - curr_seg[0]
                        dy = prev_seg[1] - curr_seg[1]

                        if i == snake_len - 1:
                            part_type = "tail"

                # Преобразуем вектор (dx, dy) в строку для поиска спрайта
                direction_key = {(0, -1): "up", (0, 1): "down", (-1, 0): "left", (1, 0): "right"}.get((dx, dy), "right")

                # --- В. Обновляем спрайт на канвасе ---
                sprite_key = (direction_key, part_type)
                sprite = self.snake_sprites.get(sprite_key)

                if sprite:
                    # itemconfig меняет картинку существующего объекта без пересоздания
                    self.canvas.itemconfig(item_id, image=sprite)

        # 4. Всплывающие эффекты
        for eff in self.effects:
            self.canvas.create_text(eff["x"], eff["y"], text=eff["text"], fill=eff["color"],
                                    font=("Arial", 16, "bold"), tags="dynamic")
            eff["y"] -= 2
            eff["life"] -= 1
        self.effects = [e for e in self.effects if e["life"] > 0]

        # 5. Оверлей паузы
        if self.is_paused:
            self.canvas.create_rectangle(0, 0, self.width_px, self.height_px, fill=self.theme["bg"],
                                         stipple="gray50", tags="dynamic")
            self.canvas.create_text(self.width_px // 2, self.height_px // 2, text="⏸ ПАУЗА",
                                    fill=self.theme["pause_text"], font=("Arial", 30, "bold"), tags="dynamic")

        self.update_info()

    # ==================== ИГРОВОЙ ЦИКЛ ====================

    def loop(self):
        if self.is_paused:
            self.render()
            self._loop_id = self.root.after(16, self.loop)
            return

        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now
        dt = min(dt, 0.1)  # Защита от скачков

        # ✅ Уменьшаем ВСЕ таймеры эффектов
        if self.magnet_effect_timer > 0:
            self.magnet_effect_timer -= 1
        if self.slow_effect_timer > 0:  # ← ДОБАВЛЕНО
            self.slow_effect_timer -= 1

        # Логический шаг (срабатывает когда прогресс >= 1.0)
        if self.move_progress >= 1.0:
            if not self.game.game_over:
                # Применяем buffered направление
                if self._pending_direction:
                    self.game.set_direction(self._pending_direction)
                    self._pending_direction = None
                event = self.game.step()
                self._handle_step_event(event)

            # Обновляем позиции для интерполяции
            self.prev_positions = list(self.curr_positions)
            self.curr_positions = [(x, y) for x, y in self.game.snake]

            # Если змейка выросла, добавляем новый сегмент (тег "snake")
            if len(self.curr_positions) > len(self.snake_items):
                tail_x, tail_y = self.curr_positions[-1]
                px, py = tail_x * self.cell_size, tail_y * self.cell_size
                sprite = self.snake_sprites.get(("right", "tail"))
                if sprite:
                    item = self.canvas.create_image(px, py, image=sprite, anchor=tk.NW, tags="snake")
                else:
                    color = self.theme["snake_body"]
                    item = self.canvas.create_rectangle(px, py, px + self.cell_size, py + self.cell_size,
                                                        fill=color, outline=self.theme["bg"], width=1, tags="snake")
                self.snake_items.append(item)

            self.move_progress = 0.0

        # Продвигаем прогресс анимации
        # ✅ Учитываем замедление при расчете длительности шага
        step_duration = self.current_delay / 1000.0
        if self.slow_effect_timer > 0:  # ← ДОБАВЛЕНО
            step_duration += 0.04  # Добавляем 40мс замедления

        self.move_progress += dt / step_duration
        if self.move_progress > 1.0:
            self.move_progress = 1.0

        # Рендер
        self.render()
        self._loop_id = self.root.after(16, self.loop)

    def _handle_step_event(self, event):
        if event == "eat":
            self.sound.play("eat")
        elif event == "die":
            self.sound.play("gameover")
            self.scores.update_score(self.player_name, self.game.score)
            self._update_leaderboard_ui()
            self.achievements.update_session_end(self.game.score, len(self.game.snake), self.session_bonuses)
            for ach in self.achievements.check_new_unlocks():
                self._show_achievement_toast(f"{ach.icon} {ach.name}", ach.desc)
        elif event in ("eat_bonus_gold", "eat_bonus_slow", "eat_bonus_magnet"):  # ✅ Добавили magnet
            self.sound.play("eat")
            self.session_bonuses += 1
            hx, hy = self.game.snake[0]
            if event == "eat_bonus_gold":
                self.effects.append({"x": hx * self.cell_size + self.cell_size / 2,
                                     "y": hy * self.cell_size + self.cell_size / 2,
                                     "text": "+5", "color": "#FFD700", "life": 30})
            elif event == "eat_bonus_slow":
                self.slow_effect_timer = 150
                self.effects.append({"x": hx * self.cell_size + self.cell_size / 2,
                                     "y": hy * self.cell_size + self.cell_size / 2,
                                     "text": "❄️ SLOW", "color": "#00BFFF", "life": 30})
            elif event == "eat_bonus_magnet":  # ✅ Обработка магнита
                self.magnet_effect_timer = 150  # 15 секунд (150 тиков * 100мс)
                self.effects.append({"x": hx * self.cell_size + self.cell_size / 2,
                                     "y": hy * self.cell_size + self.cell_size / 2,
                                     "text": "🧲 MAGNET", "color": "#FF1493", "life": 30})
        self.current_delay = max(self.min_speed, self.initial_speed - (self.game.score * self.acceleration_step))

    # ==================== УПРАВЛЕНИЕ И UI ====================

    def _apply_theme_colors(self):
        self.theme = self.THEMES[self.current_theme_name]
        self.root.configure(bg=self.theme["bg"])
        if hasattr(self, 'main_frame'):
            self.main_frame.configure(bg=self.theme["bg"])
            self.canvas.configure(bg=self.theme["bg"], highlightbackground=self.theme["grid"])
            self.info_label.configure(bg=self.theme["bg"], fg=self.theme["text"])
            if hasattr(self, 'btn_theme'):
                self.btn_theme.configure(bg=self.theme["snake_body"], fg=self.theme["bg"])

    def cycle_theme(self):
        themes = list(self.THEMES.keys())
        idx = (themes.index(self.current_theme_name) + 1) % len(themes)
        self.current_theme_name = themes[idx]
        self.config["theme_name"] = self.current_theme_name
        self._save_config()
        self._apply_theme_colors()
        self._load_wall_sprite()
        self._draw_walls()  # ✅ Перерисовываем стены только здесь
        self.render()

    def _save_config(self):
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _update_leaderboard_ui(self):
        self.lb_listbox.delete(0, tk.END)
        top = self.scores.get_leaderboard(10)
        if not top:
            self.lb_listbox.insert(tk.END, "Нет данных")
            return
        medals = ['🥇', '🥈', '🥉']
        for i, (name, score) in enumerate(top):
            self.lb_listbox.insert(tk.END, f"{medals[i] if i < 3 else f'{i + 1}.'} {name}: {score}")

    def handle_key(self, event):
        if event.keysym in ("space", "p", "P"):
            self.toggle_pause()
            return
        if event.keysym in ("a", "A"):
            self.show_achievements()
            return
        if self.is_paused:
            if event.keysym in ("t", "T"):
                self.cycle_theme()
            return
        dirs = {"Up": (0, -1), "w": (0, -1), "W": (0, -1), "Down": (0, 1), "s": (0, 1), "S": (0, 1),
                "Left": (-1, 0), "a": (-1, 0), "A": (-1, 0), "Right": (1, 0), "d": (1, 0), "D": (1, 0)}
        if event.keysym in dirs:
            self._pending_direction = dirs[event.keysym]
        elif event.keysym in ("r", "R") and self.game.game_over:
            self.restart()
        elif event.keysym in ("t", "T"):
            self.cycle_theme()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.render()

    def restart(self):
        self.game = SnakeLogic(self.config["width"], self.config["height"])
        self.current_delay = self.initial_speed
        self.slow_effect_timer = 0
        self.magnet_effect_timer = 0  # ✅ Сброс таймера магнита
        self.is_paused = False
        self.session_bonuses = 0
        self.achievements.reset_session()
        self._pending_direction = None
        self.move_progress = 0.0
        self.prev_positions = [(x, y) for x, y in self.game.snake]
        self.curr_positions = list(self.prev_positions)

        # ✅ ОЧИСТКА ПОЛЯ
        self.canvas.delete("dynamic")
        self.canvas.delete("snake")  # Удаляем старую змейку
        self.canvas.delete("walls")  # Удаляем старые стены

        # ✅ ПЕРЕОТРИСОВКА СТАТИКИ
        self._draw_walls()
        self._init_snake_canvas_items()

        self.update_info()
        self._update_leaderboard_ui()

    def update_info(self):
        best = self.scores.get_best_score(self.player_name)
        status = " | GAME OVER | R - рестарт" if self.game.game_over else ""
        pause_text = " |  ПАУЗА" if self.is_paused else ""
        # ✅ Отображаем активные эффекты
        effects_text = ""
        if self.slow_effect_timer > 0:
            effects_text += f" | 🧊 ЗАМЕДЛЕНИЕ ({self.slow_effect_timer // 10}с)"
        if self.magnet_effect_timer > 0:
            effects_text += f" | 🧲 МАГНИТ ({self.magnet_effect_timer // 10}с)"

        self.info_label.config(text=f"Счёт: {self.game.score} | Рекорд: {best}{effects_text}{status}{pause_text}")


    def _show_achievement_toast(self, title, desc):
        if self.toast_label: self.toast_label.destroy()
        self.toast_label = tk.Label(self.root, text=f"{title}\n{desc}", bg="#2a2a2a", fg="#ffd700",
                                    font=("Arial", 14, "bold"), padx=15, pady=10, relief=tk.RAISED, bd=2)
        self.toast_label.place(relx=0.5, rely=0.2, anchor="center")
        self.root.after(3000, self._hide_toast)

    def _hide_toast(self):
        if self.toast_label:
            self.toast_label.destroy()
            self.toast_label = None

    def show_achievements(self):
        win = tk.Toplevel(self.root)
        win.title("🏆 Достижения")
        win.geometry("320x420")
        win.config(bg="#1e1e1e")
        win.transient(self.root)
        win.grab_set()
        tk.Label(win, text="Ваши трофеи:", bg="#1e1e1e", fg="#fff", font=("Arial", 12, "bold")).pack(pady=10)
        frame = tk.Frame(win, bg="#1e1e1e")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for ach in self.achievements.achievements.values():
            status = "✅" if ach.unlocked else "🔒"
            color = "#00ff00" if ach.unlocked else "#666666"
            tk.Label(frame, text=f"{status} {ach.icon} {ach.name}\n   {ach.desc}",
                     bg="#1e1e1e", fg=color, justify=tk.LEFT, anchor="w", pady=6).pack(fill=tk.X)

    def _activate_test_event(self):
        """
        Активирует тестовый бонус, указанный через аргумент --event.
        Применяет эффект и создает бонус на поле для визуального теста.
        """
        if not self.test_event:
            return

        valid_events = ["eat_bonus_magnet", "eat_bonus_slow", "eat_bonus_gold"]
        if self.test_event not in valid_events:
            print(f"⚠️ Неизвестный event: {self.test_event}. Допустимые: {valid_events}")
            return

        print(f"🧪 ТЕСТОВЫЙ РЕЖИМ: Активация бонуса '{self.test_event}'")
        hx, hy = self.game.snake[0]

        if self.test_event == "eat_bonus_gold":
            # Применяем эффект: +5 очков
            self.game.score += 5
            self.effects.append({
                "x": hx * self.cell_size + self.cell_size / 2,
                "y": hy * self.cell_size + self.cell_size / 2,
                "text": "🥇 +5 (TEST)",
                "color": "#FFD700",
                "life": 60  # Увеличил для наглядности
            })
            # Создаем бонус на поле для визуального теста
            self._spawn_test_bonus_on_field("gold")

        elif self.test_event == "eat_bonus_slow":
            # Применяем эффект: замедление
            self.slow_effect_timer = 150
            self.effects.append({
                "x": hx * self.cell_size + self.cell_size / 2,
                "y": hy * self.cell_size + self.cell_size / 2,
                "text": "❄️ SLOW (TEST)",
                "color": "#00BFFF",
                "life": 60
            })
            self._spawn_test_bonus_on_field("slow")

        elif self.test_event == "eat_bonus_magnet":
            # Применяем эффект: магнит
            self.magnet_effect_timer = 150
            self.effects.append({
                "x": hx * self.cell_size + self.cell_size / 2,
                "y": hy * self.cell_size + self.cell_size / 2,
                "text": "🧲 MAGNET (TEST)",
                "color": "#FF1493",
                "life": 60
            })
            self._spawn_test_bonus_on_field("magnet")

    def _spawn_test_bonus_on_field(self, b_type):
        """Создает бонус на свободной клетке рядом со змейкой для визуального теста."""
        hx, hy = self.game.snake[0]
        # Ищем свободную клетку в радиусе 5 клеток от головы
        for radius in range(1, 6):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) != radius:
                        continue
                    nx, ny = hx + dx, hy + dy
                    if (0 <= nx < self.game.width and 0 <= ny < self.game.height and
                        (nx, ny) not in self.game.snake and
                        (nx, ny) not in self.game.walls and
                        (nx, ny) != self.game.food and
                        self.game.bonus != (nx, ny, b_type)):
                        self.game.bonus = (nx, ny, b_type)
                        self.game.bonus_ttl = 50
                        print(f"✅ Бонус '{b_type}' создан на позиции ({nx}, {ny})")
                        return
        print(f"️ Не удалось найти свободную клетку для бонуса '{b_type}'")


if __name__ == "__main__":
    # ✅ Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Змейка - тестовый режим")
    parser.add_argument(
        "--event",
        type=str,
        choices=["eat_bonus_magnet", "eat_bonus_slow", "eat_bonus_gold"],
        default=None,
        help="Активировать тестовый бонус при запуске"
    )
    args = parser.parse_args()

    config_path = "config.json"
    default_cfg = {
        "speed": 120, "min_speed": 50, "width": 20, "height": 20,
        "cell_size": 25, "score_acceleration": 2, "theme_name": "Dark"
    }
    config = default_cfg
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

    root = tk.Tk()
    root.withdraw()
    player_name = simpledialog.askstring("Вход", "Введите имя игрока:", parent=root)
    if not player_name:
        player_name = "Аноним"
    root.deiconify()

    app = SnakeApp(root, config, player_name.strip())

    # ✅ Передаем тестовый event в приложение
    if args.event:
        app.test_event = args.event
        app._activate_test_event()

    root.mainloop()