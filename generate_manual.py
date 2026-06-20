"""
Генератор Руководства пользователя для игры "Змейка".
Поддерживает форматы Markdown (.md) и PDF (.pdf).
Использует актуальные данные из snake_app.py, snake_logic.py, config.json
и спрайты из каталога /assets.
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime

# ---------------------------------------------------------------------------
# Опциональная зависимость для PDF
# ---------------------------------------------------------------------------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image as RLImage, KeepTogether
    )
    from reportlab.lib.units import cm, mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------
ASSETS_DIR = "assets"
OUTPUT_DIR = "output"
CONFIG_PATH = "config.json"

# ---------------------------------------------------------------------------
# Регистрация шрифтов с поддержкой кириллицы (для PDF)
# ---------------------------------------------------------------------------
def register_fonts():
    """Возвращает имя зарегистрированного шрифта с кириллицей."""
    if not REPORTLAB_AVAILABLE:
        return None

    candidates = [
        ("DejaVuSans", "DejaVuSans.ttf"),
        ("DejaVuSans", os.path.join("/usr/share/fonts/truetype/dejavu", "DejaVuSans.ttf")),
        ("DejaVuSans", os.path.join("/usr/share/fonts/TTF", "DejaVuSans.ttf")),
        ("DejaVuSans", os.path.join("C:\\Windows\\Fonts", "DejaVuSans.ttf")),
        ("Arial", os.path.join("C:\\Windows\\Fonts", "arial.ttf")),
        ("Arial", "/Library/Fonts/Arial.ttf"),
    ]

    for name, path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name
            except Exception:
                continue
    return None


# ---------------------------------------------------------------------------
# Загрузка актуальных данных
# ---------------------------------------------------------------------------
def load_config():
    """Загружает config.json или возвращает дефолт."""
    default = {
        "speed": 120,
        "min_speed": 50,
        "width": 20,
        "height": 20,
        "cell_size": 25,
        "score_acceleration": 2,
        "theme_name": "Dark",
        "bonus_ttl": 60,
        "slow_effect_duration": 150,
        "magnet_effect_duration": 150,
        "magnet_radius": 3,
        "bonus_blink_threshold": 15,
        "slow_step_penalty": 0.04,
        "effect_life": 30,
        "magnet_effect_life": 25,
        "test_effect_life": 60,
        "bonus_spawn_chance": 0.15,
        "wall_count": 8,
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                default.update(data)
        except Exception:
            pass
    return default


def list_available_sprites():
    """Возвращает список PNG-файлов из assets/."""
    if not os.path.isdir(ASSETS_DIR):
        return []
    return sorted(
        f for f in os.listdir(ASSETS_DIR)
        if f.lower().endswith(".png")
    )


# ---------------------------------------------------------------------------
# Генерация Markdown
# ---------------------------------------------------------------------------
def generate_markdown(config: dict, sprites: list) -> str:
    """Формирует полное руководство в формате Markdown."""
    lines = []

    def h1(t):
        lines.append(f"# {t}\n")

    def h2(t):
        lines.append(f"## {t}\n")

    def h3(t):
        lines.append(f"### {t}\n")

    def p(t):
        lines.append(f"{t}\n")

    def ul(t):
        lines.append(f"- {t}")

    def ol(t):
        lines.append(f"1. {t}")

    def code(t):
        lines.append(f"```{t}```\n")

    def table(header, rows):
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for r in rows:
            lines.append("| " + " | ".join(str(c) for c in r) + " |")
        lines.append("")

    # ---------------- Титул ----------------
    h1("🐍 SNAKE GAME — Руководство пользователя")
    p(f"**Версия:** 2.0  ")
    p(f"**Дата:** {datetime.now().strftime('%d.%m.%Y')}  ")

    # ---------------- Оглавление ----------------
    h2("📑 Оглавление")
    toc = [
        "1. Введение",
        "2. Цели и правила",
        "3. Установка и запуск",
        "4. Игровой процесс",
        "5. Бонусы",
        "6. Достижения (Ачивки)",
        "7. Начало игры",
        "8. Управление",
        "9. Интерфейс и функции",
        "10. Таблица лидеров и достижения",
        "11. Звуковое сопровождение",
        "12. Настройки (config.json)",
        "13. Решение проблем",
        "14. Технические характеристики",
    ]
    for item in toc:
        lines.append(f"- {item}")
    lines.append("")

    # ---------------- 1. Введение ----------------
    h2("1. Введение")
    p("Добро пожаловать в обновлённую игру «Змейка»! Это классическая аркада, "
      "переосмысленная с использованием современных подходов к модульности, "
      "графике и пользовательскому опыту.")
    p("Игра написана на **Python** с использованием библиотеки **Tkinter** для UI "
      "и **Pillow** для работы со спрайтами. Включает:")
    ul("Систему рекордов и таблицу лидеров")
    ul("Звуковые эффекты (Web Audio-подобный синтез)")
    ul("Динамическую сложность (ускорение по мере роста счёта)")
    ul("4 цветовые темы: Dark, Light, Matrix, Ice")
    ul("3 типа бонусов: Золотое яблоко, Снежинка, Магнит")
    ul("Систему достижений (ачивок) с отображением в панели лидеров")
    ul("Плавную анимацию движения змейки (интерполяция)")
    ul("Тестовый режим через аргумент `--event`")
    lines.append("")

    # ---------------- 2. Цели и правила ----------------
    h2("2. Цели и правила")
    h3("Цель")
    p("Набрать как можно больше очков, управляя змейкой и поедая яблоки, "
      "избегая при этом столкновений со стенами, границами поля и собственным телом.")

    h3("Правила")
    ul("Змейка движется непрерывно в выбранном направлении.")
    ul("Съеденное яблоко увеличивает длину змейки и даёт **+1 очко**.")
    ul("Скорость игры растёт с каждым съеденным яблоком.")
    ul("Столкновение с границей, стеной или собственным телом = **Game Over**.")
    ul("Бонусы появляются случайно после поедания яблока (шанс настраивается).")
    ul("Бонус исчезает, если не успеть его съесть за отведённое время.")
    lines.append("")

    # ---------------- 3. Установка и запуск ----------------
    h2("3. Установка и запуск")
    h3("Требования")
    ul("Python 3.8+")
    ul("Библиотека `Pillow` (для спрайтов): `pip install Pillow`")
    ul("Опционально: `reportlab` (для генерации PDF-руководства)")

    h3("Структура проекта")
    code("""snake_game/
├── snake_app.py          # Главный модуль (UI + игровой цикл)
├── snake_logic.py        # Игровая логика
├── sound_manager.py      # Звуковые эффекты
├── score_manager.py      # Таблица лидеров
├── achievements.py       # Система достижений
├── config.json           # Конфигурация
├── assets/               # Спрайты (PNG 25x25)
│   ├── snake_head_*.png
│   ├── snake_body_*.png
│   ├── snake_tail_*.png
│   ├── wall_*.png
│   ├── food_apple.png
│   ├── bonus_gold.png
│   ├── bonus_slow.png
│   └── bonus_magnit.png
└── output/               # Генерируемые файлы (руководство)
""")
    h3("Запуск игры")
    code("python snake_app.py")

    h3("Запуск с тестовым бонусом")
    code("python snake_app.py --event eat_bonus_magnet")
    p("Допустимые значения `--event`: `eat_bonus_gold`, `eat_bonus_slow`, `eat_bonus_magnet`.")
    lines.append("")

    # ---------------- 4. Игровой процесс ----------------
    h2("4. Игровой процесс")
    p("Игровое поле представляет собой сетку 20×20 клеток (настраивается). "
      "Змейка стартует в центре, её начальное направление выбирается **случайно** "
      "при каждом запуске.")
    p("Каждый логический шаг змейка перемещается на одну клетку. "
      "Визуально движение **плавное** благодаря интерполяции между кадрами.")
    p("На поле также расположены **стены** (8 блоков по умолчанию), "
      "которые меняют вид в зависимости от темы.")
    lines.append("")

    # ---------------- 5. Бонусы ----------------
    h2("5. Бонусы")
    p(f"После съедания обычного яблока с вероятностью "
      f"**{config.get('bonus_spawn_chance', 0.15) * 100:.0f}%** на поле появляется бонус. "
      f"Время жизни бонуса — **{config.get('bonus_ttl', 60)} тиков**. "
      "Перед исчезновением бонус начинает **мигать**.")

    table(
        ["Бонус", "Файл спрайта", "Эффект", "Длительность"],
        [
            ["🥇 Золотое яблоко", "bonus_gold.png", "+5 очков", "мгновенно"],
            ["❄️ Снежинка", "bonus_slow.png", "Замедление игры",
             f"{config.get('slow_effect_duration', 150)} тиков (~15 с)"],
            ["🧲 Магнит", "bonus_magnit.png",
             f"Притягивает еду в радиусе {config.get('magnet_radius', 3)} клеток",
             f"{config.get('magnet_effect_duration', 150)} тиков (~15 с)"],
        ],
    )

    h3("Механика магнита")
    p("Пока активен эффект магнита, еда автоматически перемещается на 1 клетку "
      "в сторону головы змейки каждый кадр. Как только еда достигает головы — "
      "она съедается (+1 очко), и появляется новое яблоко.")
    lines.append("")

    # ---------------- 6. Достижения ----------------
    h2("6. Достижения (Ачивки)")
    p("Система достижений мотивирует игрока выполнять разнообразные задачи. "
      "Прогресс сохраняется в файле `achievements.json`. "
      "**Важно:** достижения теперь отображаются непосредственно в панели лидеров "
      "в основном окне игры, что позволяет отслеживать прогресс без открытия дополнительных окон.")

    table(
        ["ID", "Название", "Описание", "Условие"],
        [
            ["first_blood", "Первая кровь", "Съешьте первый бонус", "total_bonuses ≥ 1"],
            ["speed_demon", "Демон скорости", "Наберите 30 очков за игру", "max_score ≥ 30"],
            ["marathon", "Марафонец", "Змейка вырастет до 30 сегментов", "max_length ≥ 30"],
            ["bonuses_hunter", "Охотник за бонусами", "Съешьте 3 бонуса за игру", "session_bonuses ≥ 3"],
            ["veteran", "Ветеран", "Завершите 5 игр", "games_played ≥ 5"],
        ],
    )
    p("При разблокировке достижения в центре экрана появляется всплывающее уведомление (toast).")
    lines.append("")

    # ---------------- 7. Начало игры ----------------
    h2("7. Начало игры")
    ol("Запустите `python snake_app.py`.")
    ol("В появившемся окне введите имя игрока (или нажмите OK для имени «Аноним»).")
    ol("Змейка появится в центре поля и начнёт движение в случайном направлении.")
    ol("Управляйте змейкой клавишами WASD или стрелками.")
    lines.append("")

    # ---------------- 8. Управление ----------------
    h2("8. Управление")
    table(
        ["Действие", "Клавиши"],
        [
            ["Движение вверх", "↑ / W"],
            ["Движение вниз", "↓ / S"],
            ["Движение влево", "← / A"],
            ["Движение вправо", "→ / D"],
            ["Пауза / Продолжить", "Space / P"],
            ["Смена темы", "T"],
            ["Рестарт (после Game Over)", "R"],
        ],
    )
    p("**Важно:** разворот на 180° запрещён (нельзя мгновенно пойти в противоположную сторону).")
    lines.append("")

    # ---------------- 9. Интерфейс и функции ----------------
    h2("9. Интерфейс и функции")
    h3("Основные элементы экрана")
    ul("**Игровое поле** — Canvas с сеткой, стенами, едой, бонусами и змейкой.")
    ul("**Панель лидеров** — справа от поля, показывает топ-10 игроков и достижения.")
    ul("**Информационная строка** — под полем: счёт, рекорд, активные эффекты, статус.")
    ul("**Кнопка темы** — «🎨 Тема (T)» для переключения цветовых схем.")

    h3("Цветовые темы")
    table(
        ["Тема", "Фон", "Особенность", "Спрайт стен"],
        [
            ["Dark", "#1e1e1e", "Классическая тёмная", "wall_brick.png"],
            ["Light", "#f0f0f0", "Светлая, контрастная", "wall_brick.png"],
            ["Matrix", "#000000", "Чёрная с зелёным", "wall_neon.png"],
            ["Ice", "#e0f7fa", "Ледяная, холодная", "wall_stone.png"],
        ],
    )
    lines.append("")

    # ---------------- 10. Таблица лидеров и достижения ----------------
    h2("10. Таблица лидеров и достижения")
    p("Рекорды и достижения отображаются в единой панели справа от игрового поля:")
    ul("Топ-10 игроков с лучшими результатами (с медалями 🥇🥉 для первых трёх)")
    ul("Раздел достижений текущего игрока с индикацией прогресса")
    ul("Разблокированные достижения отмечаются галочкой ✅")
    ul("Неразблокированные достижения отображаются с иконкой 🔒")
    ul("Статистика игрока: максимальный счёт, длина змейки, количество бонусов, игр")
    p("Данные сохраняются в файл `achievements.json` в формате JSON.")
    lines.append("")

    # ---------------- 11. Звуковое сопровождение ----------------
    h2("11. Звуковое сопровождение")
    p("Звуки генерируются программно через `sound_manager.py` (без внешних файлов):")
    table(
        ["Событие", "Описание"],
        [
            ["eat", "Короткий пик при поедании еды/бонуса"],
            ["gameover", "Нисходящая мелодия при проигрыше"],
        ],
    )
    lines.append("")

    # ---------------- 12. Настройки ----------------
    h2("12. Настройки (config.json)")
    p("Все параметры игры вынесены в `config.json`. Изменение значений не требует "
      "правки кода — достаточно отредактировать файл и перезапустить игру.")

    table(
        ["Параметр", "Тип", "По умолчанию", "Описание"],
        [
            ["speed", "int", config.get("speed", 120), "Начальная задержка шага (мс)"],
            ["min_speed", "int", config.get("min_speed", 50), "Минимальная задержка (макс. скорость)"],
            ["width", "int", config.get("width", 20), "Ширина поля в клетках"],
            ["height", "int", config.get("height", 20), "Высота поля в клетках"],
            ["cell_size", "int", config.get("cell_size", 25), "Размер клетки в пикселях"],
            ["score_acceleration", "int", config.get("score_acceleration", 2), "Ускорение за очко (мс)"],
            ["theme_name", "str", config.get("theme_name", "Dark"), "Тема по умолчанию"],
            ["bonus_ttl", "int", config.get("bonus_ttl", 60), "Время жизни бонуса (тики)"],
            ["slow_effect_duration", "int", config.get("slow_effect_duration", 150), "Длительность замедления (тики)"],
            ["magnet_effect_duration", "int", config.get("magnet_effect_duration", 150), "Длительность магнита (тики)"],
            ["magnet_radius", "int", config.get("magnet_radius", 3), "Радиус притяжения еды (клетки)"],
            ["bonus_blink_threshold", "int", config.get("bonus_blink_threshold", 15), "Порог мигания бонуса (тики)"],
            ["slow_step_penalty", "float", config.get("slow_step_penalty", 0.04),
             "Добавка к шагу при замедлении (сек)"],
            ["effect_life", "int", config.get("effect_life", 30), "Время жизни визуальных эффектов (кадры)"],
            ["magnet_effect_life", "int", config.get("magnet_effect_life", 25), "Время жизни эффекта магнита (кадры)"],
            ["test_effect_life", "int", config.get("test_effect_life", 60), "Время жизни тестовых эффектов (кадры)"],
            ["bonus_spawn_chance", "float", config.get("bonus_spawn_chance", 0.15), "Шанс появления бонуса (0.0–1.0)"],
            ["wall_count", "int", config.get("wall_count", 8), "Количество стен на поле"],
        ],
    )
    lines.append("")

    # ---------------- 13. Решение проблем ----------------
    h2("13. Решение проблем")
    table(
        ["Проблема", "Решение"],
        [
            ["Нет звука", "Проверьте настройки звука ОС"],
            ["Игра лагает", "Увеличьте `speed` в config.json"],
            ["Сброс рекордов", "Удалите `achievements.json` — он создастся заново"],
            ["Не запускается", "Установите Python 3.8+ и `pip install Pillow`"],
            ["Змейка не отображается", "Проверьте наличие PNG в `assets/`"],
            ["Ошибка `TclError: wrong # coordinates`", "Обновите `snake_app.py` до актуальной версии"],
            ["Бонус не исчезает", "Проверьте `bonus_ttl` и `bonus_blink_threshold`"],
        ],
    )
    lines.append("")

    # ---------------- 14. Технические характеристики ----------------
    h2("14. Технические характеристики")
    table(
        ["Параметр", "Значение"],
        [
            ["Язык программирования", "Python 3.8+"],
            ["Графическая библиотека", "Tkinter (встроена)"],
            ["Обработка изображений", "Pillow (PIL)"],
            ["Платформы", "Windows, macOS, Linux"],
            ["Размер спрайта", "25×25 пикселей, PNG, прозрачный фон"],
            ["Частота рендера", "~60 FPS (интерполяция)"],
            ["Логический шаг", "120 мс (ускоряется до 50 мс)"],
            ["Таблица лидеров", "Топ-10 игроков + достижения"],
            ["Хранение данных", "JSON-файлы (achievements.json, config.json)"],
        ],
    )
    lines.append("")

    # ---------------- Спрайты ----------------
    h2("Используемые спрайты")
    p("Игра использует PNG-спрайты размером 25×25 пикселей с прозрачным фоном "
      "из каталога `assets/`. Если спрайт не найден — используется fallback-отрисовка "
      "цветными прямоугольниками/овалами.")
    if sprites:
        table(["Файл", "Назначение"],
              [[s, _describe_sprite(s)] for s in sprites])
    else:
        p("_(Каталог `assets/` не найден или пуст.)_")
    lines.append("")

    # ---------------- Футер ----------------
    lines.append("---")
    p("**Приятной игры! 🐍**  ")
    p(f"Руководство создано {datetime.now().strftime('%d.%m.%Y')}.  ")
    p("(c) 2026 Snake Game Project")

    return "\n".join(lines)


def _describe_sprite(filename: str) -> str:
    """Краткое описание назначения спрайта по имени файла."""
    descriptions = {
        "head_up.png": "Голова змейки, смотрит вверх",
        "head_down.png": "Голова змейки, смотрит вниз",
        "head_left.png": "Голова змейки, смотрит влево",
        "head_right.png": "Голова змейки, смотрит вправо",
        "body_up.png": "Сегмент тела (вертикальный)",
        "body_down.png": "Сегмент тела (вертикальный)",
        "body_left.png": "Сегмент тела (горизонтальный)",
        "body_right.png": "Сегмент тела (горизонтальный)",
        "tail_up.png": "Хвост, смотрит вверх",
        "tail_down.png": "Хвост, смотрит вниз",
        "tail_left.png": "Хвост, смотрит влево",
        "tail_right.png": "Хвост, смотрит вправо",
        "wall_brick.png": "Кирпичная стена (темы Dark/Light)",
        "wall_stone.png": "Ледяная стена (тема Ice)",
        "wall_neon.png": "Неоновая сетка (тема Matrix)",
        "food_apple.png": "Еда — красное яблоко",
        "bonus_gold.png": "Бонус — золотое яблоко (+5 очков)",
        "bonus_slow.png": "Бонус — снежинка (замедление)",
        "bonus_magnit.png": "Бонус — магнит (притягивает еду)",
    }
    return descriptions.get(filename, "Спрайт")


# ---------------------------------------------------------------------------
# Генерация PDF (через reportlab)
# ---------------------------------------------------------------------------
def generate_pdf(markdown_text: str, output_path: str, font_name: str, sprites: list):
    """Создаёт PDF-документ из markdown-текста."""
    if not REPORTLAB_AVAILABLE:
        print("⚠️ reportlab не установлен. Установите: pip install reportlab")
        print("   Будет создан только Markdown-файл.")
        return False

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Стили с поддержкой кириллицы
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontSize=22,
        textColor=colors.darkgreen, spaceAfter=20, alignment=TA_CENTER,
        fontName=font_name, leading=26,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontSize=16,
        textColor=colors.darkblue, spaceAfter=10, spaceBefore=15,
        fontName=font_name, leading=20,
    )
    h3_style = ParagraphStyle(
        "H3", parent=styles["Heading3"], fontSize=12,
        textColor=colors.darkred, spaceAfter=8, spaceBefore=12,
        fontName=font_name, leading=16,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=10,
        textColor=colors.black, spaceAfter=6, alignment=TA_JUSTIFY,
        fontName=font_name, leading=13,
    )
    code_style = ParagraphStyle(
        "Code", parent=styles["Normal"], fontSize=9,
        textColor=colors.darkblue, backColor=colors.lightgrey,
        spaceAfter=8, spaceBefore=4, fontName=font_name, leading=11,
        leftIndent=10, rightIndent=10,
    )
    table_cell_style = ParagraphStyle(
        "TableCell", parent=styles["Normal"], fontSize=9,
        textColor=colors.black, fontName=font_name, leading=11,
        alignment=TA_LEFT,
    )

    story = []

    # Титул (без emoji)
    story.append(Paragraph("SNAKE GAME", title_style))
    story.append(Paragraph("Руководство пользователя", ParagraphStyle(
        "Sub", parent=styles["Heading2"], fontSize=16,
        textColor=colors.darkgreen, alignment=TA_CENTER,
        spaceAfter=30, fontName=font_name, leading=20,
    )))
    story.append(Spacer(1, 1 * cm))

    # Парсим markdown построчно
    in_code_block = False
    code_buffer = []

    # Буферы для таблиц
    current_table_rows = []
    current_table_cols = 0

    def wrap_text(text, max_width=40):
        """Разбивает текст на строки для переноса."""
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return "<br/>".join(lines)

    def flush_table():
        """Добавляет накопленную таблицу в документ и очищает буфер."""
        nonlocal current_table_rows, current_table_cols
        if current_table_rows:
            wrapped_data = []
            for row in current_table_rows:
                wrapped_row = []
                for cell in row:
                    if isinstance(cell, str):
                        wrapped_text = wrap_text(cell, max_width=35)
                        wrapped_row.append(Paragraph(wrapped_text, table_cell_style))
                    else:
                        wrapped_row.append(cell)
                wrapped_data.append(wrapped_row)

            # Определяем ширину колонок динамически
            num_cols = len(current_table_rows[0]) if current_table_rows else 1
            if num_cols == 2:
                col_widths = [5 * cm, 10 * cm]
            elif num_cols == 3:
                col_widths = [4 * cm, 5 * cm, 6 * cm]
            elif num_cols == 4:
                col_widths = [3.5 * cm, 3.5 * cm, 3.5 * cm, 4 * cm]
            else:
                col_widths = [4 * cm] * num_cols

            t = Table(wrapped_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * cm))

        current_table_rows = []
        current_table_cols = 0

    def flush_code():
        """Добавляет накопленный блок кода в документ."""
        nonlocal in_code_block, code_buffer
        if in_code_block and code_buffer:
            code_text = "\n".join(code_buffer).replace("`", "").strip()
            if code_text:
                story.append(Paragraph(code_text, code_style))
            code_buffer = []
            in_code_block = False

    for raw_line in markdown_text.split("\n"):
        line = raw_line.strip()

        # --- Обработка блоков кода ---
        if line.startswith("```"):
            if in_code_block:
                flush_code()
            else:
                in_code_block = True
                # Если перед блоком кода была таблица, завершаем её
                flush_table()
            continue

        if in_code_block:
            # Пустые строки внутри кода сохраняем как пробелы, чтобы не прерывать блок
            if not line:
                code_buffer.append("")
            else:
                code_buffer.append(line)
            continue

        # Пропускаем пустые строки (они служат разделителями)
        if not line:
            # Пустая строка может означать конец таблицы
            flush_table()
            story.append(Spacer(1, 0.2 * cm))
            continue

        # Заголовки
        if line.startswith("# "):
            flush_table();
            flush_code()
            text = line[2:].replace("🐍", "").replace("📑", "").replace("📦", "").strip()
            story.append(Paragraph(text, title_style))
        elif line.startswith("## "):
            flush_table();
            flush_code()
            text = line[3:].replace("🐍", "").replace("📑", "").replace("📦", "").strip()
            story.append(Paragraph(text, h2_style))
        elif line.startswith("### "):
            flush_table();
            flush_code()
            text = line[4:].replace("🐍", "").replace("📑", "").replace("📦", "").strip()
            story.append(Paragraph(text, h3_style))

        # Маркированный список
        elif line.startswith("- "):
            flush_table();
            flush_code()
            text = line[2:].replace("✓", "").replace("•", "").strip()
            story.append(Paragraph("• " + text, body_style))

        # Таблицы
        elif line.startswith("| ") and " | " in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # Пропускаем строки-разделители (---|---)
            if "---" in cells[0] or all("-" in c for c in cells):
                continue

                # Если это первая строка новой таблицы, запоминаем кол-во колонок
            if not current_table_rows:
                current_table_cols = len(cells)

            # Добавляем строку только если количество ячеек совпадает с первой строкой
            if len(cells) == current_table_cols:
                current_table_rows.append(cells)
            else:
                # Если структура нарушена, сбрасываем старую таблицу и начинаем новую
                flush_table()
                current_table_cols = len(cells)
                current_table_rows.append(cells)

        # Горизонтальный разделитель
        elif line.startswith("---"):
            flush_table(); flush_code()
            story.append(Spacer(1, 0.5 * cm))

        # Обычный текст
        else:
            flush_table(); flush_code()
            clean = line.replace("**", "").replace("_", "").replace("`", "")
            # Замена emoji на текст для PDF (сохраняем доработку без [Gold])
            replacements = {
                "🥇": "[Gold]", "❄️": "[Slow]", "🧲": "[Magnet]",
                "⏸": "[Pause]", "🏆": "[Trophy]", "🎨": "[Theme]",
                "⚠️": "[Warning]", "✅": "[OK]", "❌": "[Error]"
            }
            for emoji, txt in replacements.items():
                clean = clean.replace(emoji, txt)

            # Безопасное удаление остальных неизвестных эмодзи/символов
            safe_chars = []
            for char in clean:
                cp = ord(char)
                # Разрешаем: латиницу, кириллицу, цифры, пробелы и базовую пунктуацию
                if (cp < 128) or (0x0400 <= cp <= 0x04FF) or (0x00C0 <= cp <= 0x024F):
                    safe_chars.append(char)
            clean = "".join(safe_chars)

            story.append(Paragraph(clean, body_style))

    # Финальный сброс буферов
    flush_table()
    flush_code()

    # Добавляем изображения спрайтов
    story.append(PageBreak())
    story.append(Paragraph("Галерея спрайтов", h2_style))
    story.append(Spacer(1, 0.5 * cm))

    sprite_rows = []
    for sprite in sprites[:10]:
        path = os.path.join(ASSETS_DIR, sprite)
        if os.path.exists(path):
            try:
                img = RLImage(path, width=1.5 * cm, height=1.5 * cm)
                desc = _describe_sprite(sprite).replace("🥇", "").replace("❄️", "").replace("🧲", "")
                sprite_rows.append([img, Paragraph(desc, table_cell_style)])
            except Exception:
                sprite_rows.append([sprite, Paragraph(_describe_sprite(sprite), table_cell_style)])

    if sprite_rows:
        t = Table(sprite_rows, colWidths=[2 * cm, 14 * cm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("FONTNAME", (1, 0), (1, -1), font_name),
            ("FONTSIZE", (1, 0), (1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Приятной игры!", ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=12,
        textColor=colors.darkgreen, alignment=TA_CENTER,
        fontName=font_name,
    )))

    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Ошибка при построении PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# Копирование спрайтов в output
# ---------------------------------------------------------------------------
def copy_sprites_to_output(output_dir: str, sprites: list):
    """Копирует PNG из assets/ в output/assets/."""
    if not sprites:
        return
    assets_out = os.path.join(output_dir, "assets")
    os.makedirs(assets_out, exist_ok=True)
    for s in sprites:
        src = os.path.join(ASSETS_DIR, s)
        dst = os.path.join(assets_out, s)
        if os.path.exists(src):
            shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Генератор Руководства пользователя для игры 'Змейка'."
    )
    parser.add_argument(
        "--format", "-f",
        choices=["md", "pdf", "both"],
        default="md",
        help="Формат вывода: md (по умолчанию), pdf или both",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=OUTPUT_DIR,
        help=f"Каталог вывода (по умолчанию: {OUTPUT_DIR})",
    )
    args = parser.parse_args()

    # Подготовка
    os.makedirs(args.output_dir, exist_ok=True)
    config = load_config()
    sprites = list_available_sprites()

    print(f"📖 Генерация руководства...")
    print(f"   Формат: {args.format}")
    print(f"   Вывод:  {args.output_dir}")
    print(f"   Спрайтов найдено: {len(sprites)}")

    # Markdown
    md_text = generate_markdown(config, sprites)
    md_path = os.path.join(args.output_dir, "Snake_Game_Manual.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"✅ Markdown создан: {md_path}")

    # PDF
    if args.format in ("pdf", "both"):
        font = register_fonts()
        if font:
            pdf_path = os.path.join(args.output_dir, "Snake_Game_Manual.pdf")
            if generate_pdf(md_text, pdf_path, font, sprites):
                print(f"✅ PDF создан: {pdf_path}")
            else:
                print("⚠️ PDF не создан (см. предупреждения выше)")
        else:
            print("⚠️ Шрифт с кириллицей не найден. PDF не будет создан.")
            print("   Скачайте DejaVuSans.ttf и положите в корень проекта.")

    # Копирование спрайтов
    copy_sprites_to_output(args.output_dir, sprites)
    if sprites:
        print(f"✅ Спрайты скопированы в {args.output_dir}/assets/")

    print("\n🎉 Готово!")


if __name__ == "__main__":
    main()