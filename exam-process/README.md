# Процесс прохождения экзамена Vibe Coding 2025

Эта директория документирует процесс выполнения экзаменационного проекта по курсу Vibe Coding 2025 (ИТМО, магистратура).

## Цель экзамена

Создать работающий MVP с использованием:
- **BDD-подхода** (тесты ДО кода)
- **AI как соавтора** (Claude Code)
- **Частых коммитов** (10+, показывающих эволюцию)

**Максимальная оценка**: 25 баллов

## Этапы экзамена

### Этап 1: Планирование и выбор проекта

**Файл**: `01-project-selection-plan.md`

На этом этапе был проведен детальный анализ всех 20 предложенных проектов из задания экзамена.

**Критерии выбора:**
- Четкие требования для BDD-сценариев
- Достаточная сложность для 10+ коммитов
- Хорошая тестируемость
- Возможность показать эволюцию
- Понятная бизнес-логика

**Рассмотренные топ-3 проекта:**
1. **ПЕРЕГОВОРКИ** (#1) - Telegram бот для бронирования переговорок
2. **БЕГОВОЙ ДНЕВНИК** (#5) - CLI для трекинга пробежек
3. **СКОЛЬКО Я ДОЛЖЕН ВАСЕ** (#2) - Telegram бот для учета долгов

**Выбранный проект: ПЕРЕГОВОРКИ (#1)**

**Почему:**
- ✅ Четкие бизнес-сценарии (проверка свободных, бронирование, освобождение, запрос статуса)
- ✅ Много edge cases для тестирования (конфликты бронирований, пересечения времени)
- ✅ Естественная эволюция функционала для коммитов
- ✅ Решает реальную проблему из жизни
- ✅ Популярная технология (Telegram бот)

**Оценка потенциала: 25/25** по всем критериям:
1. Работоспособность MVP (5/5)
2. Эволюция коммитов (5/5)
3. Тесты pytest-bdd (5/5)
4. Документация (5/5)
5. Vibe Coding подход (5/5)

### Этап 2: Реализация MVP

**Статус**: ✅ Завершено (9 коммитов, 10 BDD тестов проходят)

**Детальный план**: `01-project-selection-plan.md`

**Результат**:
- Работающий Telegram бот для бронирования переговорок
- Clean Architecture (Database → Repository → Service → Bot)
- 10 BDD тестов на pytest-bdd (все зеленые)
- Полная документация (README.md + CLAUDE.md)

#### Технологический стек:
- Python 3.11
- aiogram 3.3.0 (Telegram Bot API)
- SQLite (база данных)
- pytest-bdd 6.1.1 (BDD тестирование)
- python-dotenv 1.0.0 (конфигурация)

#### Структура проекта:
```
vibe-coding-course-final/
├── exam-process/        # Документация процесса экзамена
├── src/                 # Исходный код
│   ├── bot.py          # Telegram бот
│   ├── database.py     # Работа с SQLite
│   └── models.py       # Модели данных
├── tests/              # Тесты
│   ├── features/       # BDD .feature файлы
│   └── steps/          # Step definitions
├── README.md           # Описание проекта
├── CLAUDE.md           # Инструкции для Claude Code
└── requirements.txt    # Зависимости
```

#### Git коммиты MVP (9 коммитов):
1. ✅ Initial project structure
2. ✅ Add BDD scenarios with bot commands
3. ✅ Add BDD tests with failing stubs (RED phase)
4. ✅ Implement SQLite database layer
5. ✅ Add business models for rooms and bookings
6. ✅ Implement Telegram bot with room booking commands
7. ✅ Refactor to clean architecture with Repository and Service layers
8. ✅ Add comprehensive documentation
9. ✅ Add exam process documentation

**Проверка MVP**: `pytest tests/steps/test_room_steps.py -v` → 10 passed

---

### Этап 3: Эволюции проекта (завершено)

**Файлы**: `02-evolutions-plan.md`, `03-timezone-evolution-plan.md`

**Статус**: ✅ Завершено (10 коммитов, 105 тестов проходят)

**Цель**: Подготовить проект к production deployment с полным тестовым покрытием, административными функциями и поддержкой таймзон.

#### Четыре основные эволюции:

**Evolution 1: Docker контейнеризация** ✅
- Простое развертывание через `docker-compose up`
- Конфигурация через `.env` файл (TELEGRAM_BOT_TOKEN, ADMIN_USER_ID)
- Volume для персистентности данных SQLite

**Evolution 2: Полное тестовое покрытие** ✅
- Unit тесты для Database Layer (18 тестов: CRUD, схема, конфликты)
- Unit тесты для Service Layer (31 тест: бизнес-логика, валидация, форматирование)
- Unit тесты для Admin Service (15 тестов: авторизация, управление)
- Integration тесты для Repository (14 тестов: реальный SQLite, персистентность)

**Evolution 3: Административные команды** ✅
- Таблица admins в БД с методами CRUD
- 5 admin команд в боте:
  - `/admin_add_room <название> <вместимость>` - добавить переговорку
  - `/admin_delete_room <название>` - удалить переговорку
  - `/admin_add` - добавить админа (reply to message)
  - `/admin_remove` - удалить админа (reply to message)
  - `/admin_list` - список всех админов
- Проверка прав доступа для всех admin команд
- Инициализация первого админа из ADMIN_USER_ID в .env

**Evolution 4: Timezone Management** ✅
- Таблица `settings` для конфигурационных настроек
- Методы `set_setting()` и `get_setting()` в Database и Repository layers
- Timezone-aware datetime операции в Service Layer
- Команда `/admin_set_timezone <offset>` для установки таймзоны офиса
- Все бронирования используют настроенную таймзону (по умолчанию UTC+0)
- 17 новых тестов (5 settings + 12 timezone)
- Обновленная документация с примерами timezone setup

#### Git коммиты эволюций (10 коммитов):
1. ✅ Docker + .env infrastructure
2. ✅ Unit tests for database layer (18 tests)
3. ✅ Unit tests for service layer (31 tests)
4. ✅ Integration tests for repository (14 tests)
5. ✅ Admin table and repository methods
6. ✅ Admin service layer methods with tests (15 tests)
7. ✅ Admin bot commands and documentation
8. ✅ Settings table for timezone infrastructure (5 tests)
9. ✅ Timezone management in service layer (12 tests)
10. ✅ Admin timezone command and documentation

**Итоговое количество коммитов**: 19 (9 MVP + 10 эволюций)

**Проверка эволюций**: `pytest -v` → 105 passed

## Подход к разработке

### BDD-First (Test-Driven Development)

**Ключевой принцип**: Тесты пишутся ДО кода!

1. Написать .feature файл с Gherkin-сценариями
2. Создать step definitions
3. Убедиться что тест падает (Red)
4. Написать минимальный код для прохождения теста (Green)
5. Отрефакторить (Refactor)
6. Коммит

### Работа с AI (Claude Code)

- Использование Claude для генерации кода по BDD-сценариям
- Частые коммиты после каждой реализованной фичи
- Документирование процесса работы с AI

## Чеклист для сдачи экзамена

**MVP (Этап 2)**:
- [x] Репозиторий на GitHub
- [x] README с описанием и инструкцией запуска
- [x] CLAUDE.md с описанием работы с AI
- [x] BDD .feature файлы (pytest-bdd) - 5 файлов
- [x] Тесты запускаются и проходят - 10/10 passed
- [x] 10+ коммитов с понятными сообщениями - 9 коммитов MVP
- [x] MVP работает и решает проблему заказчика

**Эволюции (Этап 3)**:
- [x] Docker + docker-compose для развертывания
- [x] Unit + Integration тесты для всех слоев (105 тестов total)
- [x] Административные команды в боте (6 команд, включая timezone)
- [x] Timezone management для корректной работы с офисным временем
- [x] Обновленная документация с инструкциями
- [x] 19 коммитов total (9 MVP + 10 эволюций)

## Реализованные BDD-сценарии

Все сценарии написаны на русском языке (Gherkin) с использованием команд Telegram бота:

### 1. **list_rooms.feature** - Просмотр всех переговорок
- Команда: `/rooms`
- Показывает список всех переговорок с вместимостью

### 2. **view_rooms.feature** - Просмотр свободных переговорок
- Команда: `/available`
- Показывает только свободные переговорки на текущий момент
- Отмечает занятые переговорки со временем освобождения

### 3. **book_room.feature** - Бронирование
- Команда: `/book <название> <время>`
- Пример: `/book Марс 15:00-16:00`
- Проверка конфликтов и пересечений времени
- Защита от двойного бронирования

### 4. **release_room.feature** - Досрочное освобождение
- Команда: `/release <название>`
- Пример: `/release Марс`
- Проверка что пользователь освобождает свою бронь

### 5. **who_booked.feature** - Запрос статуса переговорки
- Команда: `/status <название>`
- Пример: `/status Марс`
- Показывает кто забронировал и до какого времени

### Дополнительные команды (планируются):
- `/start` - приветствие и список команд
- `/mybooks` - мои активные бронирования

---

**Начало экзамена**: 2026-01-14
**Отведенное время**: 3 часа
**Инструмент**: Claude Code (Sonnet 4.5)
