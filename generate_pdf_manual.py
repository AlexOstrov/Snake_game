from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import sys

# Создаем директорию output если не существует
os.makedirs('output', exist_ok=True)


# ============================================
# РЕГИСТРАЦИЯ ШРИФТОВ С ПОДДЕРЖКОЙ КИРИЛЛИЦЫ
# ============================================

def register_fonts():
    """
    Регистрирует шрифты с поддержкой кириллицы.
    Возвращает имена зарегистрированных шрифтов.
    """
    fonts_registered = {}

    # Список шрифтов для поиска
    font_candidates = [
        # Windows
        ("DejaVuSans", "C:\\Windows\\Fonts\\DejaVuSans.ttf"),
        ("Arial", "C:\\Windows\\Fonts\\arial.ttf"),
        ("TimesNewRoman", "C:\\Windows\\Fonts\\times.ttf"),
        ("CourierNew", "C:\\Windows\\Fonts\\cour.ttf"),
        ("SegoeUI", "C:\\Windows\\Fonts\\segoeui.ttf"),

        # macOS
        ("DejaVuSans", "/Library/Fonts/DejaVuSans.ttf"),
        ("Arial", "/Library/Fonts/Arial.ttf"),
        ("Helvetica", "/Library/Fonts/Helvetica.ttf"),

        # Linux
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("DejaVuSans", "/usr/share/fonts/TTF/DejaVuSans.ttf"),
        ("LiberationSans", "/usr/share/fonts/liberation/LiberationSans-Regular.ttf"),
    ]

    # Пробуем зарегистрировать основной шрифт
    for font_name, font_path in font_candidates:
        if os.path.exists(font_path) and font_name not in fonts_registered:
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                fonts_registered[font_name] = font_path
                print(f"✅ Шрифт: {font_name}")
            except Exception as e:
                pass

    # Пробуем найти шрифты в текущей директории
    local_fonts = {
        "DejaVuSans": "DejaVuSans.ttf",
        "Arial": "Arial.ttf",
        "TimesNewRoman": "times.ttf",
        "CourierNew": "cour.ttf"
    }

    for font_name, font_file in local_fonts.items():
        if os.path.exists(font_file) and font_name not in fonts_registered:
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_file))
                fonts_registered[font_name] = font_file
                print(f"✅ Локальный шрифт: {font_name}")
            except:
                pass

    return fonts_registered


# Регистрируем шрифты
registered_fonts = register_fonts()

if not registered_fonts:
    print("\n" + "=" * 60)
    print("ОШИБКА: Не найдены шрифты с поддержкой кириллицы!")
    print("=" * 60)
    print("\nСкачайте DejaVuSans.ttf:")
    print("https://github.com/dejavu-fonts/dejavu-fonts/releases")
    print("Или используйте Arial.ttf / Times.ttf")
    print("=" * 60)
    sys.exit(1)

# Выбираем основной шрифт
MAIN_FONT = list(registered_fonts.keys())[0]
print(f"\n🔤 Основной шрифт: {MAIN_FONT}")

# Создаем PDF документ
doc = SimpleDocTemplate("output/Snake_Game_User_Manual.pdf",
                        pagesize=A4,
                        rightMargin=2 * cm,
                        leftMargin=2 * cm,
                        topMargin=2 * cm,
                        bottomMargin=2 * cm)

# Стили
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.darkgreen,
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName=MAIN_FONT,
    leading=28
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=colors.darkblue,
    spaceAfter=12,
    spaceBefore=20,
    fontName=MAIN_FONT,
    leading=20
)

subheading_style = ParagraphStyle(
    'CustomSubHeading',
    parent=styles['Heading3'],
    fontSize=12,
    textColor=colors.darkred,
    spaceAfter=10,
    spaceBefore=15,
    fontName=MAIN_FONT,
    leading=16
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=11,
    textColor=colors.black,
    spaceAfter=8,
    alignment=TA_JUSTIFY,
    fontName=MAIN_FONT,
    leading=14
)

code_style = ParagraphStyle(
    'CodeStyle',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.darkblue,
    backColor=colors.lightgrey,
    spaceAfter=10,
    spaceBefore=5,
    fontName=MAIN_FONT,
    leading=12
)

# Контент документа
story = []

# Титульная страница
story.append(Paragraph("SNAKE GAME", title_style))
story.append(Paragraph("Руководство пользователя",
                       ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=18,
                                      textColor=colors.darkgreen, alignment=TA_CENTER, spaceAfter=50,
                                      fontName=MAIN_FONT, leading=22)))
story.append(Spacer(1, 2 * cm))
story.append(Paragraph("Версия 2.0", normal_style))
story.append(Paragraph("Написано с помощью ИИ-агентов", normal_style))
story.append(Spacer(1, 1 * cm))

# Оглавление
story.append(Paragraph("ОГЛАВЛЕНИЕ", heading_style))
toc_items = [
    "1. Введение",
    "2. Установка и запуск",
    "3. Игровой процесс",
    "   3.1. Начало игры",
    "   3.2. Управление",
    "   3.3. Цели и правила",
    "4. Интерфейс и функции",
    "   4.1. Таблица лидеров",
    "   4.2. Звуковое сопровождение",
    "   4.3. Настройки (config.json)",
    "5. Решение проблем",
    "6. Технические характеристики"
]
for item in toc_items:
    story.append(Paragraph(item, normal_style))
story.append(PageBreak())

# Раздел 1
story.append(Paragraph("1. ВВЕДЕНИЕ", heading_style))
story.append(Paragraph(
    "Добро пожаловать в обновлённую игру «Змейка»! Это классическая аркада, "
    "переосмысленная с использованием современных подходов к модульности и пользовательскому опыту. "
    "Игра написана на Python, не требует установки дополнительных библиотек (кроме стандартной) и включает:",
    normal_style
))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("[*] Систему рекордов и таблицу лидеров", normal_style))
story.append(Paragraph("[*] Звуковые эффекты", normal_style))
story.append(Paragraph("[*] Динамическую сложность (ускорение)", normal_style))
story.append(Paragraph("[*] Красивый графический интерфейс", normal_style))
story.append(Spacer(1, 0.5 * cm))

# Раздел 2
story.append(Paragraph("2. УСТАНОВКА И ЗАПУСК", heading_style))
story.append(Paragraph(
    "Для запуска игры не требуется подключение к интернету или установка сторонних пакетов.",
    normal_style
))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("Требования:", subheading_style))
story.append(Paragraph("* Python 3.6 или выше", normal_style))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("Инструкция по запуску:", subheading_style))
story.append(Paragraph("1. Скопируйте все файлы проекта в одну папку:", normal_style))

files_data = [
    ['snake_app.py', 'Основной файл запуска'],
    ['snake_logic.py', 'Игровая логика'],
    ['sound_manager.py', 'Управление звуком'],
    ['score_manager.py', 'Система рекордов'],
    ['config.json', 'Файл конфигурации']
]

files_table = Table(files_data, colWidths=[4 * cm, 8 * cm])
files_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, -1), MAIN_FONT),  # ВАЖНО: применяем ко ВСЕМ ячейкам
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
]))
story.append(files_table)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("2. Откройте терминал/командную строку в этой папке", normal_style))
story.append(Paragraph("3. Выполните команду:", normal_style))
story.append(Paragraph("python snake_app.py", code_style))
story.append(Spacer(1, 0.5 * cm))

# Раздел 3
story.append(Paragraph("3. ИГРОВОЙ ПРОЦЕСС", heading_style))
story.append(Paragraph("3.1. Начало игры", subheading_style))
story.append(Paragraph(
    "При запуске появится окно с запросом имени игрока. Введите ваш никнейм "
    "(например, Alex). Если оставить поле пустым, будет использовано имя Аноним. "
    "Змейка появляется в центре поля.",
    normal_style
))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("3.2. Управление", subheading_style))
story.append(Paragraph("Используйте клавиатуру для управления движением:", normal_style))

controls_data = [
    ['Стрелки вверх/вниз/влево/вправо', 'Клавиши со стрелками'],
    ['W A S D', 'Альтернативное управление'],
    ['R', 'Перезапуск игры (после проигрыша)']
]

controls_table = Table(controls_data, colWidths=[3 * cm, 9 * cm])
controls_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, -1), MAIN_FONT),  # ВСЕ ячейки
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
]))
story.append(controls_table)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("3.3. Цели и правила", subheading_style))
story.append(
    Paragraph("(Еда) Красный кружок: Съедайте еду, чтобы увеличивать длину змейки и получать очки (+1 за единицу).",
              normal_style))
story.append(Paragraph("(Смерть) Игра заканчивается, если вы врезаетесь в стену или в собственное тело.", normal_style))
story.append(Paragraph(
    "(Ускорение) С каждым съеденным яблоком игра немного ускоряется. Начальная скорость комфортная, но к высокому счёту реакция потребуется мгновенная.",
    normal_style))
story.append(Spacer(1, 0.5 * cm))

# Раздел 4
story.append(Paragraph("4. ИНТЕРФЕЙС И ФУНКЦИИ", heading_style))
story.append(Paragraph("4.1. Таблица лидеров", subheading_style))
story.append(Paragraph("Справа от игрового поля расположена панель «Лидеры».", normal_style))
story.append(Paragraph("* Отображаются топ-10 игроков с лучшими результатами", normal_style))
story.append(Paragraph("* Данные сохраняются автоматически в файл scores.json", normal_style))
story.append(Paragraph("* При завершении игры ваш результат сравнивается с таблицей", normal_style))
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("4.2. Звуковое сопровождение", subheading_style))
story.append(Paragraph("Игра включает 4 типа звуковых сигналов:", normal_style))

sounds_data = [
    ['[1] Щелчок', 'При каждом движении (тик)'],
    ['[2] Пик', 'При поедании еды'],
    ['[3] Гул', 'При ударе о стену'],
    ['[4] Мелодия', 'При завершении игры (Game Over)']
]

sounds_table = Table(sounds_data, colWidths=[3 * cm, 9 * cm])
sounds_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, -1), MAIN_FONT),  # ВСЕ ячейки
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
]))
story.append(sounds_table)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph("4.3. Настройки (config.json)", subheading_style))

config_data = [
    ['"speed"', 'Начальная задержка в мс', '120'],
    ['"min_speed"', 'Предел максимальной скорости', '50'],
    ['"width"', 'Ширина поля в клетках', '20'],
    ['"height"', 'Высота поля в клетках', '20'],
    ['"cell_size"', 'Размер клетки в пикселях', '25'],
    ['"score_acceleration"', 'Ускорение за очко (мс)', '2']
]

config_table = Table(config_data, colWidths=[3 * cm, 7 * cm, 2 * cm])
config_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, -1), MAIN_FONT),  # ВСЕ ячейки
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
]))
story.append(config_table)
story.append(Spacer(1, 0.5 * cm))

# Раздел 5
story.append(Paragraph("5. РЕШЕНИЕ ПРОБЛЕМ", heading_style))

problems_data = [
    ['Проблема', 'Решение'],
    ['Нет звука', 'Проверьте настройки звука ОС'],
    ['Игра лагает', 'Увеличьте "speed" в config.json'],
    ['Сброс рекордов', 'Удалите scores.json, он создастся заново'],
    ['Не запускается', 'Установите Python 3.6+']
]

problems_table = Table(problems_data, colWidths=[5 * cm, 7 * cm])
problems_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, -1), MAIN_FONT),  # ВСЕ ячейки
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
]))
story.append(problems_table)
story.append(Spacer(1, 0.5 * cm))

# Раздел 6
story.append(Paragraph("6. ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ", heading_style))

tech_data = [
    ['Язык программирования', 'Python 3.6+'],
    ['Графическая библиотека', 'Tkinter (встроена в Python)'],
    ['Платформы', 'Windows, macOS, Linux'],
    ['Таблица лидеров', 'Топ-10 игроков'],
    ['Максимальная скорость', '50 мс между кадрами']
]

tech_table = Table(tech_data, colWidths=[6 * cm, 6 * cm])
tech_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, -1), MAIN_FONT),  # ВСЕ ячейки
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
]))
story.append(tech_table)
story.append(Spacer(1, 1 * cm))

# Заключение
story.append(PageBreak())
story.append(Paragraph("ПРИЯТНОЙ ИГРЫ!", heading_style))
story.append(Paragraph(
    "Если у вас возникли вопросы или предложения по улучшению игры, вы можете модифицировать код самостоятельно или обратиться к документации Python.",
    normal_style))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("Руководство создано с помощью ИИ-агентов", normal_style))
story.append(Paragraph("(c) 2026 Snake Game Project", normal_style))

# Генерация PDF
try:
    doc.build(story)
    print("\n" + "=" * 60)
    print("УСПЕХ! PDF руководство создано!")
    print("=" * 60)
    print(f"Путь: output/Snake_Game_User_Manual.pdf")
    print(f"Размер: {os.path.getsize('output/Snake_Game_User_Manual.pdf') / 1024:.2f} KB")
    print(f"Шрифт: {MAIN_FONT}")
    print("=" * 60)
except Exception as e:
    print(f"\nОШИБКА при создании PDF: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)