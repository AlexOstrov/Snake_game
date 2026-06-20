"""
Главный модуль приложения игры "Змейка".

Содержит класс SnakeApp, который управляет:
- Отображением игры на Canvas
- Обработкой пользовательского ввода
- Игровым циклом
- Управлением темами и эффектами

Все визуальные параметры настраиваются через THEMES и config.json.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os
import time
import random
import argparse
from PIL import Image, ImageTk
from typing import Dict, List, Optional, Tuple

from snake_logic import SnakeLogic
from sound_manager import SoundManager
from achievements import AchievementsManager


class FloatingText:
    """
    Класс для создания всплывающего текста (эффекты +5, SLOW и т.д.).

    Attributes:
        canvas: Canvas для отрисовки
        x: Начальная позиция X
        y: Начальная позиция Y
        life: Время жизни эффекта в кадрах
    """

    def __init__(
            self,
            canvas: tk.Canvas,
            x: float,
            y: float,
            text: str,
            color: str = "yellow"
    ):
        """
        Инициализация всплывающего текста.

        Args:
            canvas: Canvas для отрисовки
            x: Позиция X
            y: Позиция Y
            text: Текст для отображения
            color: Цвет текста
        """
        self.canvas = canvas
        self.x = x
        self.y = y
        self.life = 35
        self.id = self.canvas.create_text(
            x, y,
            text=text,
            fill=color,
            font=("Arial", 16, "bold")
        )
        self.animate()

    def animate(self) -> None:
        """Анимация движения текста вверх и исчезновения."""
        self.y -= 2
        self.canvas.coords(self.id, self.x, self.y)
        self.life -= 1

        if self.life > 0:
            self.canvas.winfo_toplevel().after(50, self.animate)
        else:
            self.canvas.delete(self.id)


class SnakeApp:
    """
    Главное приложение игры "Змейка".

    Управляет игровым циклом, отрисовкой, вводом пользователя
    и всеми игровыми механиками.
    """

    # Конфигурация тем
    THEMES: Dict[str, Dict[str, str]] = {
        "Dark": {
            "bg": "#1e1e1e",
            "snake_head": "#00ff00",
            "snake_body": "#00cc00",
            "food": "#ff3333",
            "text": "#ffffff",
            "grid": "#333333",
            "pause_text": "#ffffff",
            "wall": "#555555",
            "bonus_gold": "#ffd700",
            "bonus_slow": "#00bfff",
            "bonus_magnet": "#FF1493"
        },
        "Light": {
            "bg": "#f0f0f0",
            "snake_head": "#333333",
            "snake_body": "#666666",
            "food": "#e91e63",
            "text": "#000000",
            "grid": "#cccccc",
            "pause_text": "#000000",
            "wall": "#888888",
            "bonus_gold": "#ffaa00",
            "bonus_slow": "#0077ff",
            "bonus_magnet": "#FF1493"
        },
        "Matrix": {
            "bg": "#000000",
            "snake_head": "#00ff00",
            "snake_body": "#008800",
            "food": "#00ff00",
            "text": "#00ff00",
            "grid": "#003300",
            "pause_text": "#00ff00",
            "wall": "#004400",
            "bonus_gold": "#ffd700",
            "bonus_slow": "#00ffff",
            "bonus_magnet": "#FF1493"
        },
        "Ice": {
            "bg": "#e0f7fa",
            "snake_head": "#006064",
            "snake_body": "#00838f",
            "food": "#ff6f00",
            "text": "#006064",
            "grid": "#b2ebf2",
            "pause_text": "#006064",
            "wall": "#81d4fa",
            "bonus_gold": "#ff6f00",
            "bonus_slow": "#00bfff",
            "bonus_magnet": "#FF1493"
        }
    }

    # Маппинг направлений для спрайтов
    DIRECTION_MAP = {
        (0, -1): "up",
        (0, 1): "down",
        (-1, 0): "left",
        (1, 0): "right"
    }

    def __init__(
            self,
            root: tk.Tk,
            config: Dict,
            player_name: str
    ):
        """
        Инициализация приложения.

        Args:
            root: Корневое окно Tkinter
            config: Словарь конфигурации
            player_name: Имя игрока
        """
        # 1. Инициализация root
        self.root = root
        self.config = config
        self.player_name = player_name

        # Параметры скорости из конфига
        self.initial_speed = config["speed"]
        self.min_speed = config.get("min_speed", 50)
        self.acceleration_step = config.get("score_acceleration", 2)

        # Тема
        self.current_theme_name = config.get("theme_name", "Dark")
        if self.current_theme_name not in self.THEMES:
            self.current_theme_name = "Dark"

        # 2. Инициализация игровой логики
        bonus_blink_threshold = config.get("bonus_blink_threshold", 15)
        bonus_ttl = config.get("bonus_ttl", 60)
        self.game = SnakeLogic(
            width=config["width"],
            height=config["height"],
            bonus_ttl=bonus_ttl,
            bonus_blink_threshold=bonus_blink_threshold
        )
        self.cell_size = config["cell_size"]

        # 3. Загрузка графики
        self.snake_sprites: Dict[Tuple[str, str], ImageTk.PhotoImage] = {}
        self._load_snake_sprites()
        self._load_wall_sprite()
        self._load_bonus_sprites()
        self._load_food_sprite()

        # Защита спрайтов от сборщика мусора
        self._sprite_refs = [
            self.snake_sprites,
            getattr(self, 'wall_sprite', None),
            getattr(self, 'bonus_gold_sprite', None),
            getattr(self, 'bonus_slow_sprite', None),
            getattr(self, 'bonus_magnet_sprite', None),
            getattr(self, 'food_sprite', None)
        ]

        # 4. Менеджеры
        self.sound = SoundManager()
        self.achievements = AchievementsManager(player_name)

        # 5. Состояние игры
        self.is_paused = False
        self.session_bonuses = 0
        self.toast_label: Optional[tk.Label] = None
        self.effects: List[Dict] = []
        self.slow_effect_timer = 0
        self.magnet_effect_timer = 0
        # Параметры эффектов из конфига
        self.slow_effect_duration = config.get("slow_effect_duration", 150)
        self.magnet_effect_duration = config.get("magnet_effect_duration", 150)
        self.magnet_radius = config.get("magnet_radius", 3)
        self.bonus_blink_threshold = config.get("bonus_blink_threshold", 15)
        self.slow_step_penalty = config.get("slow_step_penalty", 0.04)
        self.effect_life = config.get("effect_life", 30)
        self.magnet_effect_life = config.get("magnet_effect_life", 25)
        self.test_effect_life = config.get("test_effect_life", 60)

        # 6. Анимация движения
        self.prev_positions: List[Tuple[int, int]] = [
            (x, y) for x, y in self.game.snake
        ]
        self.curr_positions: List[Tuple[int, int]] = list(self.prev_positions)
        self.snake_items: List[int] = []  # ID объектов Canvas
        self.move_progress = 0.0
        self._last_time = time.perf_counter()
        self._pending_direction: Optional[Tuple[int, int]] = None

        # 7. Применение темы и создание UI
        self._apply_theme_colors()
        self.root.title(f"Змейка | Игрок: {player_name}")
        self.root.resizable(False, False)

        # Основной фрейм
        self.main_frame = tk.Frame(root, bg=self.theme["bg"])
        self.main_frame.pack(padx=10, pady=10)

        # Canvas для игры
        self.width_px = self.game.width * self.cell_size
        self.height_px = self.game.height * self.cell_size
        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.width_px,
            height=self.height_px,
            bg=self.theme["bg"],
            highlightthickness=1,
            highlightbackground=self.theme["grid"]
        )
        self.canvas.grid(row=0, column=0, rowspan=2)

        # Инициализация статических объектов
        self._draw_walls()
        self._init_snake_canvas_items()

        # Фрейм лидеров
        self.leaderboard_frame = tk.Frame(
            self.main_frame,
            bg=self.theme["bg"],
            width=250,
            height=self.height_px
        )
        self.leaderboard_frame.grid(row=0, column=1, rowspan=2, padx=10, sticky="ns")
        self.leaderboard_frame.grid_propagate(False)

        tk.Label(
            self.leaderboard_frame,
            text="🏆 Лидеры",
            fg=self.theme["text"],
            bg=self.theme["bg"],
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 5))

        self.lb_listbox = tk.Listbox(
            self.leaderboard_frame,
            bg=self.theme["bg"],
            fg=self.theme["text"],
            font=("Courier", 10),
            borderwidth=0,
            highlightthickness=0
        )
        self.lb_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._update_leaderboard_ui()

        # Фрейм кнопок управления
        self.controls_frame = tk.Frame(
            self.main_frame,
            bg=self.theme["bg"]
        )
        self.controls_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        self.btn_theme = tk.Button(
            self.controls_frame,
            text="🎨 Тема (T)",
            command=self.cycle_theme,
            bg=self.theme.get("snake_body", "#ccc"),
            fg=self.theme.get("bg", "#000")
        )
        self.btn_theme.pack(side=tk.LEFT, padx=5)

        # Информационная метка
        self.info_label = tk.Label(
            self.main_frame,
            text="",
            fg=self.theme["text"],
            bg=self.theme["bg"],
            font=("Arial", 12)
        )
        self.info_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

        # Игровой цикл
        self.current_delay = self.initial_speed
        self._loop_id: Optional[str] = None
        self.root.bind("<Key>", self.handle_key)

        # Тестовый режим
        self.test_event: Optional[str] = None
        self._activate_test_event()

        # Запуск цикла
        self.loop()

    # ==================== МЕТОДЫ ЗАГРУЗКИ ГРАФИКИ ====================

    def _load_snake_sprites(self) -> None:
        """Загрузка спрайтов змейки (голова, тело, хвост для 4 направлений)."""
        parts = ["head", "body", "tail"]
        directions = ["up", "down", "left", "right"]
        size = (self.cell_size, self.cell_size)

        try:
            for part in parts:
                for direction in directions:
                    filename = f"assets/{part}_{direction}.png"
                    if os.path.exists(filename):
                        img = Image.open(filename).resize(
                            size, Image.Resampling.LANCZOS
                        ).convert("RGBA")
                        self.snake_sprites[(direction, part)] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Ошибка загрузки графики змейки: {e}")

    def _load_wall_sprite(self) -> None:
        """Загрузка спрайта стены в зависимости от текущей темы."""
        try:
            # Выбор файла стены по теме
            wall_file_map = {
                "Dark": "assets/wall_brick.png",
                "Light": "assets/wall_brick.png",
                "Ice": "assets/wall_stone.png",
                "Matrix": "assets/wall_neon.png"
            }
            wall_file = wall_file_map.get(self.current_theme_name, "assets/wall_brick.png")

            if os.path.exists(wall_file):
                wall_img = Image.open(wall_file).resize(
                    (self.cell_size, self.cell_size),
                    Image.Resampling.LANCZOS
                ).convert("RGBA")
                self.wall_sprite = ImageTk.PhotoImage(wall_img)
            else:
                self.wall_sprite = None
        except Exception:
            self.wall_sprite = None

    def _load_bonus_sprites(self) -> None:
        """Загрузка спрайтов бонусов (золото, замедление, магнит)."""
        try:
            size = (self.cell_size, self.cell_size)

            # Словарь файлов бонусов
            bonus_files = {
                "gold": "assets/bonus_gold.png",
                "slow": "assets/bonus_slow.png",
                "magnet": "assets/bonus_magnit.png"
            }

            # Атрибуты для хранения спрайтов
            sprite_attrs = {
                "gold": "bonus_gold_sprite",
                "slow": "bonus_slow_sprite",
                "magnet": "bonus_magnet_sprite"
            }

            for bonus_type, filename in bonus_files.items():
                attr_name = sprite_attrs[bonus_type]
                if os.path.exists(filename):
                    img = Image.open(filename).resize(
                        size, Image.Resampling.LANCZOS
                    ).convert("RGBA")
                    setattr(self, attr_name, ImageTk.PhotoImage(img))
                else:
                    setattr(self, attr_name, None)

        except Exception:
            self.bonus_gold_sprite = None
            self.bonus_slow_sprite = None
            self.bonus_magnet_sprite = None

    def _load_food_sprite(self) -> None:
        """Загрузка спрайта еды (красное яблоко)."""
        try:
            size = (self.cell_size, self.cell_size)
            food_path = "assets/food_apple.png"

            if os.path.exists(food_path):
                food_img = Image.open(food_path).resize(
                    size, Image.Resampling.LANCZOS
                ).convert("RGBA")
                self.food_sprite = ImageTk.PhotoImage(food_img)

                # Добавляем в защиту от сборщика мусора
                if not hasattr(self, '_sprite_refs'):
                    self._sprite_refs = []
                self._sprite_refs.append(self.food_sprite)
            else:
                self.food_sprite = None
        except Exception as e:
            print(f"Ошибка загрузки спрайта еды: {e}")
            self.food_sprite = None

    # ==================== МЕТОДЫ ОТРИСОВКИ ====================

    def _draw_walls(self) -> None:
        """Отрисовка стен (вызывается при старте, рестарте или смене темы)."""
        self.canvas.delete("walls")

        for x, y in self.game.walls:
            px, py = x * self.cell_size, y * self.cell_size

            if hasattr(self, 'wall_sprite') and self.wall_sprite:
                self.canvas.create_image(
                    px, py,
                    image=self.wall_sprite,
                    anchor=tk.NW,
                    tags="walls"
                )
            else:
                # Fallback: прямоугольник
                self.canvas.create_rectangle(
                    px, py,
                    px + self.cell_size,
                    py + self.cell_size,
                    fill=self.theme.get("wall", "#555"),
                    outline="#000",
                    tags="walls"
                )

    def _init_snake_canvas_items(self) -> None:
        """Создание Canvas-элементов для змейки (тег 'snake').
        Начальное направление выбирается случайным образом."""
        self.snake_items = []

        # ✅ Выбираем случайное начальное направление
        random_dir_str = random.choice(["up", "down", "left", "right"])
        dir_to_vector = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        # ✅ Синхронизируем случайное направление с игровой логикой
        self.game.direction = dir_to_vector[random_dir_str]

        for i, (x, y) in enumerate(self.game.snake):
            px, py = x * self.cell_size, y * self.cell_size

            # Определяем тип сегмента
            if i == 0:
                part_type = "head"
            elif i == len(self.game.snake) - 1:
                part_type = "tail"
            else:
                part_type = "body"

            # ✅ Для головы используем случайное направление, для остальных — дефолтное
            direction_str = random_dir_str if i == 0 else "right"
            sprite_key = (direction_str, part_type)
            sprite = self.snake_sprites.get(sprite_key)

            if sprite:
                item = self.canvas.create_image(
                    px, py,
                    image=sprite,
                    anchor=tk.NW,
                    tags="snake"
                )
            else:
                # Fallback: прямоугольник
                color = self.theme["snake_head"] if i == 0 else self.theme["snake_body"]
                item = self.canvas.create_rectangle(
                    px, py,
                    px + self.cell_size,
                    py + self.cell_size,
                    fill=color,
                    outline=self.theme["bg"],
                    width=1,
                    tags="snake"
                )

            self.snake_items.append(item)

    def render(self) -> None:
        """
        Основной метод отрисовки.
        Обновляет только динамические объекты (еда, бонусы, эффекты, пауза).
        Статические объекты (стены, змейка) обновляются отдельно.
        """
        # Удаляем только динамику
        self.canvas.delete("dynamic")

        # === ЭФФЕКТ МАГНИТА ===
        if self.magnet_effect_timer > 0:
            self._apply_magnet_effect()

        # === ОТРИСОВКА ЕДЫ ===
        self._draw_food()

        # === ОТРИСОВКА БОНУСОВ ===
        if self.game.bonus:
            self._draw_bonus()

        # === ОТРИСОВКА ЗМЕЙКИ ===
        self._draw_snake()

        # === ВСПЛЫВАЮЩИЕ ЭФФЕКТЫ ===
        self._draw_effects()

        # === ОВЕРЛЕЙ ПАУЗЫ ===
        if self.is_paused:
            self._draw_pause_overlay()

        self.update_info()

    def _apply_magnet_effect(self) -> None:
        """Применение эффекта магнита: притягивание еды к голове змейки."""
        head_x, head_y = self.game.snake[0]
        food_x, food_y = self.game.food

        # Вычисляем расстояние (манхэттенское)
        distance = abs(head_x - food_x) + abs(head_y - food_y)

        # Если еда в радиусе действия магнита
        if 0 < distance <= self.magnet_radius:
            # Двигаем еду к голове
            if food_x < head_x:
                food_x += 1
            elif food_x > head_x:
                food_x -= 1

            if food_y < head_y:
                food_y += 1
            elif food_y > head_y:
                food_y -= 1

            # Если еда достигла головы - съедаем её
            if food_x == head_x and food_y == head_y:
                self.game.score += 1
                self.game.food = self.game._spawn_food()
                self.sound.play("eat")

                # Визуальный эффект
                self.effects.append({
                    "x": head_x * self.cell_size + self.cell_size / 2,
                    "y": head_y * self.cell_size + self.cell_size / 2,
                    "text": " +1",
                    "color": "#FF1493",
                    "life": self.magnet_effect_life
                })
            else:
                # Просто двигаем еду
                self.game.food = (food_x, food_y)

    def _draw_food(self) -> None:
        """Отрисовка еды (спрайт или fallback)."""
        fx, fy = self.game.food
        px, py = fx * self.cell_size, fy * self.cell_size

        if hasattr(self, 'food_sprite') and self.food_sprite:
            self.canvas.create_image(
                px, py,
                image=self.food_sprite,
                anchor=tk.NW,
                tags="dynamic"
            )
        else:
            # Fallback: овал
            self.canvas.create_oval(
                px, py,
                px + self.cell_size,
                py + self.cell_size,
                fill=self.theme["food"],
                tags="dynamic"
            )

    def _draw_bonus(self) -> None:
        """Отрисовка бонуса с эффектом мигания перед исчезновением."""
        bx, by, b_type = self.game.bonus

        # Проверяем, нужно ли скрыть бонус (мигание)
        is_blinking = self.game.bonus_ttl < self.bonus_blink_threshold and (self.game.bonus_ttl // 3) % 2 == 0

        if not is_blinking:
            px, py = bx * self.cell_size, by * self.cell_size

            # Выбираем цвет и спрайт по типу бонуса
            color = self.theme.get(f"bonus_{b_type}", "#FF1493")
            sprite = self._get_bonus_sprite(b_type)

            if sprite:
                self.canvas.create_image(
                    px, py,
                    image=sprite,
                    anchor=tk.NW,
                    tags="dynamic"
                )
            else:
                # Fallback: овал
                self.canvas.create_oval(
                    px + 2, py + 2,
                    px + self.cell_size - 2,
                    py + self.cell_size - 2,
                    fill=color,
                    outline="white",
                    width=2,
                    tags="dynamic"
                )

    def _get_bonus_sprite(self, b_type: str) -> Optional[ImageTk.PhotoImage]:
        """
        Получить спрайт бонуса по типу.

        Args:
            b_type: Тип бонуса ("gold", "slow", "magnet")

        Returns:
            Спрайт или None
        """
        sprite_map = {
            "gold": getattr(self, 'bonus_gold_sprite', None),
            "slow": getattr(self, 'bonus_slow_sprite', None),
            "magnet": getattr(self, 'bonus_magnet_sprite', None)
        }
        return sprite_map.get(b_type)

    def _draw_snake(self) -> None:
        """Отрисовка змейки с интерполяцией и динамической сменой спрайтов."""
        snake_len = len(self.snake_items)

        for i, item_id in enumerate(self.snake_items):
            if i >= len(self.prev_positions) or i >= len(self.curr_positions):
                continue

            # === А. Вычисляем координаты (плавное движение) ===
            px_prev, py_prev = self.prev_positions[i]
            px_curr, py_curr = self.curr_positions[i]

            interp_x = px_prev + (px_curr - px_prev) * self.move_progress
            interp_y = py_prev + (py_curr - py_prev) * self.move_progress

            # === Б. Вычисляем направление и тип части ===
            part_type, dx, dy = self._get_snake_segment_info(i, snake_len)

            # === В. Обновляем спрайт и координаты ===
            direction_key = self.DIRECTION_MAP.get((dx, dy), "right")
            sprite_key = (direction_key, part_type)
            sprite = self.snake_sprites.get(sprite_key)

            # Проверяем тип объекта и обновляем соответствующим образом
            obj_type = self.canvas.type(item_id)

            if obj_type == "image":
                # Для изображений: 2 координаты (x, y)
                self.canvas.coords(
                    item_id,
                    interp_x * self.cell_size,
                    interp_y * self.cell_size
                )
                if sprite:
                    self.canvas.itemconfig(item_id, image=sprite)
            elif obj_type == "rectangle":
                # Для прямоугольников: 4 координаты (x1, y1, x2, y2)
                self.canvas.coords(
                    item_id,
                    interp_x * self.cell_size,
                    interp_y * self.cell_size,
                    interp_x * self.cell_size + self.cell_size,
                    interp_y * self.cell_size + self.cell_size
                )
                # Обновляем цвет
                color = self.theme["snake_head"] if part_type == "head" else self.theme["snake_body"]
                self.canvas.itemconfig(item_id, fill=color, outline=self.theme["bg"])

    def _get_snake_segment_info(
            self,
            index: int,
            snake_len: int
    ) -> Tuple[str, int, int]:
        """
        Получить информацию о сегменте змейки.

        Args:
            index: Индекс сегмента
            snake_len: Общая длина змейки

        Returns:
            Кортеж (part_type, dx, dy)
        """
        if index == 0:
            # Голова смотрит в направлении движения
            return "head", *self.game.direction
        elif index < len(self.game.snake):
            # Тело/хвост смотрят на предыдущий сегмент
            prev_seg = self.game.snake[index - 1]
            curr_seg = self.game.snake[index]
            dx = prev_seg[0] - curr_seg[0]
            dy = prev_seg[1] - curr_seg[1]

            part_type = "tail" if index == snake_len - 1 else "body"
            return part_type, dx, dy

        return "body", 0, 0

    def _draw_effects(self) -> None:
        """Отрисовка и обновление всплывающих эффектов."""
        for eff in self.effects:
            self.canvas.create_text(
                eff["x"], eff["y"],
                text=eff["text"],
                fill=eff["color"],
                font=("Arial", 16, "bold"),
                tags="dynamic"
            )
            eff["y"] -= 2
            eff["life"] -= 1

        # Удаляем завершившиеся эффекты
        self.effects = [e for e in self.effects if e["life"] > 0]

    def _draw_pause_overlay(self) -> None:
        """Отрисовка оверлея паузы."""
        self.canvas.create_rectangle(
            0, 0,
            self.width_px, self.height_px,
            fill=self.theme["bg"],
            stipple="gray50",
            tags="dynamic"
        )
        self.canvas.create_text(
            self.width_px // 2, self.height_px // 2,
            text="⏸ ПАУЗА",
            fill=self.theme["pause_text"],
            font=("Arial", 30, "bold"),
            tags="dynamic"
        )

    # ==================== ИГРОВОЙ ЦИКЛ ====================

    def loop(self) -> None:
        """Основной игровой цикл (вызывается ~60 раз в секунду)."""
        if self.is_paused:
            self.render()
            self._loop_id = self.root.after(16, self.loop)
            return

        # Вычисляем delta time
        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now
        dt = min(dt, 0.1)  # Защита от скачков

        # Уменьшаем таймеры эффектов
        if self.magnet_effect_timer > 0:
            self.magnet_effect_timer -= 1
        if self.slow_effect_timer > 0:
            self.slow_effect_timer -= 1

        # Логический шаг (когда прогресс >= 1.0)
        if self.move_progress >= 1.0:
            if not self.game.game_over:
                # Применяем буферизованное направление
                if self._pending_direction:
                    self.game.set_direction(self._pending_direction)
                    self._pending_direction = None

                event = self.game.step()
                self._handle_step_event(event)

            # Обновляем позиции для интерполяции
            self.prev_positions = list(self.curr_positions)
            self.curr_positions = [(x, y) for x, y in self.game.snake]

            # Если змейка выросла, добавляем новый сегмент
            if len(self.curr_positions) > len(self.snake_items):
                self._add_snake_segment()

            self.move_progress = 0.0

        # Продвигаем прогресс анимации
        step_duration = self.current_delay / 1000.0

        # Учитываем замедление
        if self.slow_effect_timer > 0:
            step_duration += self.slow_step_penalty

        self.move_progress = min(self.move_progress + dt / step_duration, 1.0)

        # Рендер и следующий кадр
        self.render()
        self._loop_id = self.root.after(16, self.loop)

    def _add_snake_segment(self) -> None:
        """Добавление нового сегмента хвоста при росте змейки."""
        tail_x, tail_y = self.curr_positions[-1]
        px, py = tail_x * self.cell_size, tail_y * self.cell_size

        # Временный спрайт (render исправит направление)
        sprite = self.snake_sprites.get(("right", "tail"))

        if sprite:
            item = self.canvas.create_image(
                px, py,
                image=sprite,
                anchor=tk.NW,
                tags="snake"
            )
        else:
            # Fallback: прямоугольник
            item = self.canvas.create_rectangle(
                px, py,
                px + self.cell_size,
                py + self.cell_size,
                fill=self.theme["snake_body"],
                outline=self.theme["bg"],
                width=1,
                tags="snake"
            )

        self.snake_items.append(item)

    def _handle_step_event(self, event: str) -> None:
        """
        Обработка событий игрового шага.
        """
        if event == "eat":
            self.sound.play("eat")
            # ✅ Обновляем UI в реальном времени (счёт, длина, марафонец)
            self._update_live_stats()

        elif event == "die":
            self.sound.play("gameover")
            # Финальное обновление статистики при смерти
            self.achievements.update_session_end(
                self.game.score,
                len(self.game.snake),
                self.session_bonuses
            )
            # Финальная проверка достижений
            for ach in self.achievements.check_new_unlocks():
                self._show_achievement_toast(f"{ach.icon} {ach.name}", ach.desc)
            self._update_leaderboard_ui()

        elif event in ("eat_bonus_gold", "eat_bonus_slow", "eat_bonus_magnet"):
            self.sound.play("eat")
            self.session_bonuses += 1
            hx, hy = self.game.snake[0]

            if event == "eat_bonus_gold":
                self.effects.append({
                    "x": hx * self.cell_size + self.cell_size / 2,
                    "y": hy * self.cell_size + self.cell_size / 2,
                    "text": "+5",
                    "color": "#FFD700",
                    "life": 30
                })

            elif event == "eat_bonus_slow":
                self.slow_effect_timer = self.slow_effect_duration
                self.effects.append({
                    "x": hx * self.cell_size + self.cell_size / 2,
                    "y": hy * self.cell_size + self.cell_size / 2,
                    "text": "❄️ SLOW",
                    "color": "#00BFFF",
                    "life": 30
                })

            elif event == "eat_bonus_magnet":
                self.magnet_effect_timer = self.magnet_effect_duration
                self.effects.append({
                    "x": hx * self.cell_size + self.cell_size / 2,
                    "y": hy * self.cell_size + self.cell_size / 2,
                    "text": "🧲 MAGNET",
                    "color": "#FF1493",
                    "life": 30
                })

            # ✅ Обновляем UI в реальном времени (бонусы, охотник за бонусами, первая кровь)
            self._update_live_stats()

        # Ускорение от очков
        self.current_delay = max(
            self.min_speed,
            self.initial_speed - (self.game.score * self.acceleration_step)
        )

    # ==================== УПРАВЛЕНИЕ И UI ====================

    def _apply_theme_colors(self) -> None:
        """Применение цветов текущей темы к элементам интерфейса."""
        self.theme = self.THEMES[self.current_theme_name]
        self.root.configure(bg=self.theme["bg"])

        if hasattr(self, 'main_frame'):
            self.main_frame.configure(bg=self.theme["bg"])
            self.canvas.configure(
                bg=self.theme["bg"],
                highlightbackground=self.theme["grid"]
            )
            self.info_label.configure(
                bg=self.theme["bg"],
                fg=self.theme["text"]
            )
            if hasattr(self, 'btn_theme'):
                self.btn_theme.configure(
                    bg=self.theme["snake_body"],
                    fg=self.theme["bg"]
                )

    def cycle_theme(self) -> None:
        """Переключение на следующую тему."""
        themes = list(self.THEMES.keys())
        idx = (themes.index(self.current_theme_name) + 1) % len(themes)
        self.current_theme_name = themes[idx]

        self.config["theme_name"] = self.current_theme_name
        self._save_config()

        self._apply_theme_colors()
        self._load_wall_sprite()
        self._draw_walls()
        self.render()

    def _save_config(self) -> None:
        """Сохранение текущей конфигурации в файл."""
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _update_leaderboard_ui(self) -> None:
        """Обновление списка лидеров и достижений текущего игрока в одной панели."""
        self.lb_listbox.delete(0, tk.END)

        # ═══════════════════════════════════════════
        # РАЗДЕЛ 1: ТАБЛИЦА ЛИДЕРОВ
        # ═══════════════════════════════════════════

        top = self.achievements.get_leaderboard(10)
        if not top:
            self.lb_listbox.insert(tk.END, "  Нет данных")
        else:
            medals = ['🥇', '🥈', '🥉']
            for i, (name, score) in enumerate(top):
                prefix = medals[i] if i < 3 else f"{i + 1}."
                # Выделяем текущего игрока
                if name == self.player_name:
                    self.lb_listbox.insert(tk.END, f"▶ {prefix} {name}: {score} ◀")
                else:
                    self.lb_listbox.insert(tk.END, f"  {prefix} {name}: {score}")

        # ═══════════════════════════════════════════
        # РАЗДЕЛ 2: ДОСТИЖЕНИЯ ИГРОКА
        # ═══════════════════════════════════════════
        self.lb_listbox.insert(tk.END, "")
        self.lb_listbox.insert(tk.END, "═════════════════════════")
        self.lb_listbox.insert(tk.END, "🎯 ДОСТИЖЕНИЯ!")
        self.lb_listbox.insert(tk.END, f"   Игрок: {self.player_name}")
        self.lb_listbox.insert(tk.END, "═════════════════════════")

        # Разблокированные достижения
        self.lb_listbox.insert(tk.END, "")
        self.lb_listbox.insert(tk.END, "✅ Разблокированные:")
        unlocked = [ach for ach in self.achievements.achievements.values() if ach.unlocked]
        if unlocked:
            for ach in unlocked:
                icon = f"{ach.icon} " if ach.icon else ""
                self.lb_listbox.insert(tk.END, f"  • {icon}{ach.name}")
        else:
            self.lb_listbox.insert(tk.END, "  (пока нет)")

        # Неразблокированные достижения
        self.lb_listbox.insert(tk.END, "")
        self.lb_listbox.insert(tk.END, "🔒 Неразблокированные:")
        locked = [ach for ach in self.achievements.achievements.values() if not ach.unlocked]
        if locked:
            for ach in locked:
                icon = f"{ach.icon} " if ach.icon else ""
                self.lb_listbox.insert(tk.END, f"  • {icon}{ach.name}")
        else:
            self.lb_listbox.insert(tk.END, "  (все открыты!)")

        # Статистика игрока
        self.lb_listbox.insert(tk.END, "")
        self.lb_listbox.insert(tk.END, "📊 Статистика:")
        stats = self.achievements.stats
        self.lb_listbox.insert(tk.END, f"  • Макс. счёт: {stats.get('max_score', 0)}")
        self.lb_listbox.insert(tk.END, f"  • Макс. длина: {stats.get('max_length', 0)}")
        self.lb_listbox.insert(tk.END, f"  • Бонусов: {stats.get('total_bonuses', 0)}")
        self.lb_listbox.insert(tk.END, f"  • Игр сыграно: {stats.get('games_played', 0)}")

    def handle_key(self, event: tk.Event) -> None:
        """
        Обработчик нажатий клавиш.

        Args:
            event: Событие клавиатуры
        """
        # Пауза
        if event.keysym in ("space", "p", "P"):
            self.toggle_pause()
            return

        # Управление в паузе
        if self.is_paused:
            if event.keysym in ("t", "T"):
                self.cycle_theme()
            return

        # Направления движения
        dirs = {
            "Up": (0, -1), "w": (0, -1), "W": (0, -1),
            "Down": (0, 1), "s": (0, 1), "S": (0, 1),
            "Left": (-1, 0), "a": (-1, 0), "A": (-1, 0),
            "Right": (1, 0), "d": (1, 0), "D": (1, 0)
        }

        if event.keysym in dirs:
            self._pending_direction = dirs[event.keysym]
        elif event.keysym in ("r", "R") and self.game.game_over:
            self.restart()
        elif event.keysym in ("t", "T"):
            self.cycle_theme()

    def toggle_pause(self) -> None:
        """Переключение состояния паузы."""
        self.is_paused = not self.is_paused
        self.render()

    def restart(self) -> None:
        """Перезапуск игры."""
        # Пересоздаём логику
        bonus_ttl = self.config.get("bonus_ttl", 60)
        bonus_blink_threshold = self.config.get("bonus_blink_threshold", 15)
        self.game = SnakeLogic(
            self.config["width"],
            self.config["height"],
            bonus_ttl=bonus_ttl,
            bonus_blink_threshold=bonus_blink_threshold
        )

        # Сброс состояния
        self.current_delay = self.initial_speed
        self.slow_effect_timer = 0
        self.magnet_effect_timer = 0
        self.is_paused = False
        self.session_bonuses = 0
        self.achievements.reset_session()
        self._pending_direction = None
        self.move_progress = 0.0

        # Сброс позиций анимации
        self.prev_positions = [(x, y) for x, y in self.game.snake]
        self.curr_positions = list(self.prev_positions)

        # Очистка поля
        self.canvas.delete("dynamic")
        self.canvas.delete("snake")
        self.canvas.delete("walls")

        # Перерисовка статики
        self._draw_walls()
        self._init_snake_canvas_items()

        self.update_info()
        self._update_leaderboard_ui()

    def _update_live_stats(self) -> None:
        """
        Обновляет статистику, проверяет достижения и обновляет UI
        в реальном времени во время игры.
        """
        # 1. Обновляем live-статистику (max_score, max_length, session_bonuses)
        self.achievements.update_live_stats(
            self.game.score,
            len(self.game.snake),
            self.session_bonuses
        )

        # 2. Проверяем новые достижения (сразу показываем тосты)
        for ach in self.achievements.check_new_unlocks():
            self._show_achievement_toast(f"{ach.icon} {ach.name}", ach.desc)

        # 3. Обновляем панель лидеров и достижений
        self._update_leaderboard_ui()

    def update_info(self) -> None:
        """Обновление информационной метки."""
        best = self.achievements.get_best_score(self.player_name)
        status = " | GAME OVER | R - рестарт" if self.game.game_over else ""
        pause_text = " | ⏸ ПАУЗА" if self.is_paused else ""

        # Активные эффекты
        effects_text = ""
        if self.slow_effect_timer > 0:
            effects_text += f" | 🧊 ЗАМЕДЛЕНИЕ ({self.slow_effect_timer // 10}с)"
        if self.magnet_effect_timer > 0:
            effects_text += f" | 🧲 МАГНИТ ({self.magnet_effect_timer // 10}с)"

        self.info_label.config(
            text=f"Счёт: {self.game.score} | Рекорд: {best}{effects_text}{status}{pause_text}"
        )

    def _show_achievement_toast(self, title: str, desc: str) -> None:
        """
        Показать временное уведомление о достижении.

        Args:
            title: Заголовок достижения
            desc: Описание достижения
        """
        if self.toast_label:
            self.toast_label.destroy()

        self.toast_label = tk.Label(
            self.root,
            text=f"{title}\n{desc}",
            bg="#2a2a2a",
            fg="#ffd700",
            font=("Arial", 14, "bold"),
            padx=15,
            pady=10,
            relief=tk.RAISED,
            bd=2
        )
        self.toast_label.place(relx=0.5, rely=0.2, anchor="center")
        self.root.after(3000, self._hide_toast)

    def _hide_toast(self) -> None:
        """Скрыть уведомление о достижении."""
        if self.toast_label:
            self.toast_label.destroy()
            self.toast_label = None


    def _activate_test_event(self) -> None:
        """Активация тестового бонуса (если указан через --event)."""
        if not self.test_event:
            return

        valid_events = ["eat_bonus_magnet", "eat_bonus_slow", "eat_bonus_gold"]
        if self.test_event not in valid_events:
            print(f"⚠️ Неизвестный event: {self.test_event}. Допустимые: {valid_events}")
            return

        print(f" ТЕСТОВЫЙ РЕЖИМ: Активация бонуса '{self.test_event}'")
        hx, hy = self.game.snake[0]

        if self.test_event == "eat_bonus_gold":
            self.game.score += 5
            self.effects.append({
                "x": hx * self.cell_size + self.cell_size / 2,
                "y": hy * self.cell_size + self.cell_size / 2,
                "text": " +5 (TEST)",
                "color": "#FFD700",
                "life": self.test_effect_life
            })
            self._spawn_test_bonus_on_field("gold")

        elif self.test_event == "eat_bonus_slow":
            self.slow_effect_timer = self.SLOW_EFFECT_DURATION
            self.effects.append({
                "x": hx * self.cell_size + self.cell_size / 2,
                "y": hy * self.cell_size + self.cell_size / 2,
                "text": "❄️ SLOW (TEST)",
                "color": "#00BFFF",
                "life": 60
            })
            self._spawn_test_bonus_on_field("slow")

        elif self.test_event == "eat_bonus_magnet":
            self.magnet_effect_timer = self.MAGNET_EFFECT_DURATION
            self.effects.append({
                "x": hx * self.cell_size + self.cell_size / 2,
                "y": hy * self.cell_size + self.cell_size / 2,
                "text": "🧲 MAGNET (TEST)",
                "color": "#FF1493",
                "life": 60
            })
            self._spawn_test_bonus_on_field("magnet")

    def _spawn_test_bonus_on_field(self, b_type: str) -> None:
        """
        Создать бонус на свободной клетке рядом со змейкой для теста.

        Args:
            b_type: Тип бонуса
        """
        hx, hy = self.game.snake[0]

        # Ищем свободную клетку в радиусе 5 клеток
        for radius in range(1, 6):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) != radius:
                        continue

                    nx, ny = hx + dx, hy + dy

                    if (0 <= nx < self.game.width and
                            0 <= ny < self.game.height and
                            (nx, ny) not in self.game.snake and
                            (nx, ny) not in self.game.walls and
                            (nx, ny) != self.game.food and
                            self.game.bonus != (nx, ny, b_type)):
                        self.game.bonus = (nx, ny, b_type)
                        self.game.bonus_ttl = self.game.bonus_ttl_default
                        print(f"✅ Бонус '{b_type}' создан на позиции ({nx}, {ny})")
                        return

        print(f"⚠️ Не удалось найти свободную клетку для бонуса '{b_type}'")


# ==================== ТОЧКА ВХОДА ====================

if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Змейка - тестовый режим")
    parser.add_argument(
        "--event",
        type=str,
        choices=["eat_bonus_magnet", "eat_bonus_slow", "eat_bonus_gold"],
        default=None,
        help="Активировать тестовый бонус при запуске"
    )
    args = parser.parse_args()

    # Загрузка конфигурации
    config_path = "config.json"
    default_cfg = {
        "speed": 120,
        "min_speed": 50,
        "width": 20,
        "height": 20,
        "cell_size": 25,
        "score_acceleration": 2,
        "theme_name": "Dark",
        "bonus_ttl": 60
    }

    config = default_cfg
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

    # Создание окна
    root = tk.Tk()
    root.withdraw()

    player_name = simpledialog.askstring(
        "Вход",
        "Введите имя игрока:",
        parent=root
    )
    if not player_name:
        player_name = "Аноним"

    root.deiconify()

    # Запуск игры
    app = SnakeApp(root, config, player_name.strip())

    # Активация тестового режима
    if args.event:
        app.test_event = args.event
        app._activate_test_event()

    root.mainloop()