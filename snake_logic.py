import random


class SnakeLogic:
    # ✅ Добавляем параметр bonus_ttl
    def __init__(self, width=20, height=20, bonus_ttl=50):
        self.width = width
        self.height = height
        self.snake = [(width // 2, height // 2)]
        self.direction = (1, 0)

        self.walls = set()
        self._generate_walls(8)

        self.bonus = None
        self.bonus_ttl = 0
        self.bonus_ttl_default = bonus_ttl  # ✅ Сохраняем значение из конфига

        self.food = self._spawn_food()
        self.score = 0
        self.game_over = False

    def _generate_walls(self, count):
        """Генерирует случайные стены, не перекрывая стартовую позицию змейки."""
        safe_zone = [(x, y) for x in range(self.width // 2 - 2, self.width // 2 + 3)
                     for y in range(self.height // 2 - 2, self.height // 2 + 3)]

        attempts = 0
        while len(self.walls) < count and attempts < 100:
            pos = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if pos not in safe_zone and pos not in self.walls:
                self.walls.add(pos)
            attempts += 1

    def _spawn_food(self):
        """Детерминированный поиск свободной клетки для еды."""
        free_cells = []
        for x in range(self.width):
            for y in range(self.height):
                pos = (x, y)
                if pos not in self.snake and pos not in self.walls:
                    free_cells.append(pos)

        if not free_cells:
            print("⚠️ Нет свободных клеток для еды!")
            return 0, 0  # ✅ Более питонично

        return random.choice(free_cells)

    def _spawn_bonus(self):
        # ✅ Если бонус уже активен — выходим, не трогаем его
        if self.bonus is not None:
            return
        """Создает бонус на свободном месте с защитой от бесконечного цикла."""
        free_cells = []
        for x in range(self.width):
            for y in range(self.height):
                pos = (x, y)
                if (pos not in self.snake and
                        pos not in self.walls and
                        pos != self.food and
                        pos != self.bonus):
                    free_cells.append(pos)

        if not free_cells:
            print("⚠️ Нет свободных клеток для бонуса!")
            return

        pos = random.choice(free_cells)
        b_type = random.choice(["gold", "slow", "magnet"])
        self.bonus = (pos[0], pos[1], b_type)
        # ✅ Используем значение из конфига вместо хардкода
        self.bonus_ttl = self.bonus_ttl_default

    def set_direction(self, new_dir):
        if new_dir != (-self.direction[0], -self.direction[1]):
            self.direction = new_dir

    def step(self):
        if self.game_over:
            return "none"

        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # 1. Проверка стен (смерть)
        if new_head in self.walls:
            self.game_over = True
            return "die"

        # 2. Проверка границ поля
        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.game_over = True
            return "die"

        # 3. Проверка столкновения с хвостом
        if new_head in self.snake:
            self.game_over = True
            return "die"

        self.snake.insert(0, new_head)
        event = "move"

        # 4. Проверка еды
        if new_head == self.food:
            self.score += 1
            self.food = self._spawn_food()
            event = "eat"

            # Шанс появления бонуса после еды (15%)
            if random.random() < 0.15:
                self._spawn_bonus()

        # 5. Проверка бонуса
        elif self.bonus and new_head == (self.bonus[0], self.bonus[1]):
            b_type = self.bonus[2]
            if b_type == "gold":
                self.score += 5
                self.bonus = None
                return "eat_bonus_gold"
            elif b_type == "slow":
                self.bonus = None
                return "eat_bonus_slow"
            elif b_type == "magnet":
                self.bonus = None
                return "eat_bonus_magnet"
        else:
            self.snake.pop()

        # 6. Таймер бонуса (если бонус существует, уменьшаем время)
        if self.bonus:
            self.bonus_ttl -= 1
            if self.bonus_ttl <= 0:
                self.bonus = None

        return event