"""
Модуль игровой логики змейки.

Содержит класс SnakeLogic, который управляет:
- Движением змейки
- Генерацией еды и бонусов
- Обнаружением столкновений
- Подсчётом очков

Все параметры настраиваются через конструктор или config.json.
"""

import random
from typing import Tuple, Set, Optional, List


class SnakeLogic:
    """
    Класс игровой логики змейки.

    Attributes:
        width: Ширина игрового поля в клетках
        height: Высота игрового поля в клетках
        snake: Список координат сегментов змейки [(x, y), ...]
        direction: Текущее направление движения (dx, dy)
        walls: Множество координат стен
        bonus: Текущий бонус (x, y, type) или None
        food: Координаты еды (x, y)
        score: Текущий счёт игрока
        game_over: Флаг окончания игры
    """

    # Константы направлений
    DIRECTION_UP = (0, -1)
    DIRECTION_DOWN = (0, 1)
    DIRECTION_LEFT = (-1, 0)
    DIRECTION_RIGHT = (1, 0)

    # Типы бонусов
    BONUS_GOLD = "gold"
    BONUS_SLOW = "slow"
    BONUS_MAGNET = "magnet"

    def __init__(
            self,
            width: int = 20,
            height: int = 20,
            bonus_ttl: int = 50,
            wall_count: int = 8,
            bonus_spawn_chance: float = 0.15,
            bonus_blink_threshold: int = 15
    ):
        """
        Инициализация игровой логики.

        Args:
            width: Ширина поля (по умолчанию 20)
            height: Высота поля (по умолчанию 20)
            bonus_ttl: Время жизни бонуса в тиках (по умолчанию 50)
            wall_count: Количество стен на поле (по умолчанию 8)
            bonus_spawn_chance: Шанс появления бонуса при съедании еды (0.0-1.0)
        """
        self.width = width
        self.height = height
        self.bonus_ttl_default = bonus_ttl
        self.wall_count = wall_count
        self.bonus_spawn_chance = bonus_spawn_chance
        self.bonus_blink_threshold = bonus_blink_threshold

        # Инициализация змейки в центре поля
        self.snake: List[Tuple[int, int]] = [(width // 2, height // 2)]
        self.direction: Tuple[int, int] = self.DIRECTION_RIGHT

        # Игровые объекты
        self.walls: Set[Tuple[int, int]] = set()
        self._generate_walls(wall_count)

        self.bonus: Optional[Tuple[int, int, str]] = None
        self.bonus_ttl: int = 0

        self.food: Tuple[int, int] = self._spawn_food()
        self.score: int = 0
        self.game_over: bool = False

    def _get_free_cells(
            self,
            exclude_snake: bool = True,
            exclude_walls: bool = True,
            exclude_food: bool = False,
            exclude_bonus: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Получить список свободных клеток на поле.

        Args:
            exclude_snake: Исключить клетки, занятые змейкой
            exclude_walls: Исключить клетки со стенами
            exclude_food: Исключить клетку с едой
            exclude_bonus: Исключить клетку с бонусом

        Returns:
            Список координат свободных клеток
        """
        free_cells = []

        for x in range(self.width):
            for y in range(self.height):
                pos = (x, y)

                # Проверяем все условия исключения
                if exclude_snake and pos in self.snake:
                    continue
                if exclude_walls and pos in self.walls:
                    continue
                if exclude_food and pos == self.food:
                    continue
                if exclude_bonus and pos == (self.bonus[0], self.bonus[1]) if self.bonus else False:
                    continue

                free_cells.append(pos)

        return free_cells

    def _generate_walls(self, count: int) -> None:
        """
        Генерация случайных стен на поле.

        Стены не размещаются в безопасной зоне вокруг стартовой позиции змейки.

        Args:
            count: Количество стен для генерации
        """
        # Безопасная зона: 5x5 клеток вокруг центра
        center_x, center_y = self.width // 2, self.height // 2
        safe_zone = {
            (x, y)
            for x in range(center_x - 2, center_x + 3)
            for y in range(center_y - 2, center_y + 3)
        }

        attempts = 0
        max_attempts = 100

        while len(self.walls) < count and attempts < max_attempts:
            pos = (
                random.randint(0, self.width - 1),
                random.randint(0, self.height - 1)
            )

            if pos not in safe_zone and pos not in self.walls:
                self.walls.add(pos)

            attempts += 1

    def _spawn_food(self) -> Tuple[int, int]:
        """
        Разместить еду на случайной свободной клетке.

        Returns:
            Координаты еды (x, y)
        """
        free_cells = self._get_free_cells(
            exclude_snake=True,
            exclude_walls=True
        )

        if not free_cells:
            print("️ Нет свободных клеток для еды!")
            return (0, 0)

        return random.choice(free_cells)

    def _spawn_bonus(self) -> None:
        """
        Разместить бонус на случайной свободной клетке.

        Бонус не размещается, если уже существует активный бонус.
        Тип бонуса выбирается случайно из доступных типов.
        """
        # Не создаём новый бонус, если текущий ещё активен
        if self.bonus is not None:
            return

        free_cells = self._get_free_cells(
            exclude_snake=True,
            exclude_walls=True,
            exclude_food=True,
            exclude_bonus=True
        )

        if not free_cells:
            print("️ Нет свободных клеток для бонуса!")
            return

        # Выбираем случайную клетку и тип бонуса
        pos = random.choice(free_cells)
        b_type = random.choice([self.BONUS_GOLD, self.BONUS_SLOW, self.BONUS_MAGNET])

        self.bonus = (pos[0], pos[1], b_type)
        self.bonus_ttl = self.bonus_ttl_default

    def set_direction(self, new_dir: Tuple[int, int]) -> None:
        """
        Установить новое направление движения.

        Разворот на 180° запрещён.

        Args:
            new_dir: Новое направление (dx, dy)
        """
        # Запрещаем разворот на 180°
        opposite_dir = (-self.direction[0], -self.direction[1])
        if new_dir != opposite_dir:
            self.direction = new_dir

    def step(self) -> str:
        """
        Выполнить один шаг игры.

        Returns:
            Событие шага: "none", "move", "eat", "die",
                         "eat_bonus_gold", "eat_bonus_slow", "eat_bonus_magnet"
        """
        if self.game_over:
            return "none"

        # Вычисляем новую позицию головы
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Проверка столкновения со стенами
        if new_head in self.walls:
            self.game_over = True
            return "die"

        # Проверка выхода за границы поля
        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.game_over = True
            return "die"

        # Проверка столкновения с собой
        if new_head in self.snake:
            self.game_over = True
            return "die"

        # Двигаем змейку
        self.snake.insert(0, new_head)
        event = "move"

        # Проверяем съедание еды
        if new_head == self.food:
            self.score += 1
            self.food = self._spawn_food()
            event = "eat"

            # С шансом создаём бонус
            if random.random() < self.bonus_spawn_chance:
                self._spawn_bonus()

        # Проверяем съедание бонуса
        elif self.bonus and new_head == (self.bonus[0], self.bonus[1]):
            b_type = self.bonus[2]

            if b_type == self.BONUS_GOLD:
                self.score += 5
                self.bonus = None
                return "eat_bonus_gold"
            elif b_type == self.BONUS_SLOW:
                self.bonus = None
                return "eat_bonus_slow"
            elif b_type == self.BONUS_MAGNET:
                self.bonus = None
                return "eat_bonus_magnet"

        # Если ничего не съели, удаляем хвост
        else:
            self.snake.pop()

        # Уменьшаем TTL бонуса
        if self.bonus:
            self.bonus_ttl -= 1
            if self.bonus_ttl <= 0:
                self.bonus = None

        return event