# Evolution 5: Service Layer Refactoring (Рефакторинг бота на Service Layer)

## Проблема

Бот обходил Service Layer и работал напрямую с Database и Models, что привело к:

1. **Дублирование логики**: Код бота повторял логику сервиса
2. **Баг с таймзоной**: Бот использовал `datetime.now()` вместо `self.service.now()`
3. **Нарушение архитектуры**: Clean Architecture предполагает один путь к данным
4. **Технический долг**: Два независимых подключения к БД

### Диагностика проблемы

**Архитектура была задумана так:**
```
bot.py → service.py → repository.py → database.py
```

**Но реально бот работал так:**
```
bot.py → models.py → database.py     (почти все команды)
bot.py → service.py → repository.py  (только timezone)
```

### Конкретные проблемы по командам

| Команда | Использовал | Должен использовать | Баг с timezone |
|---------|-------------|---------------------|----------------|
| `/rooms` | `Room.get_all(self.db)` | `self.service.list_all_rooms()` | — |
| `/available` | `datetime.now()` + `Room.get_all()` | `self.service.list_available_rooms()` | **ДА** |
| `/book` | `datetime.now().date()` + `Booking.create()` | `self.service.book_room()` | **ДА** |
| `/release` | `self.db.find_booking_by_room_and_user()` | `self.service.release_room()` | — |
| `/status` | `datetime.now()` + `room.get_current_booking()` | `self.service.get_room_status()` | **ДА** |
| `/mybooks` | `Booking.get_user_bookings()` | `self.service.get_user_bookings()` | — |
| admin команды | `self.db.*` напрямую | `self.service.*` | — |

### Корень проблемы

В `bot.py:27-31` создавались **два независимых подключения** к данным:

```python
self.db = Database(db_path)                    # Прямой доступ к БД
self.repository = SQLiteRepository(db_path)   # Для service layer
self.service = RoomBookingService(self.repository)
```

## Решение

Полный рефакторинг бота для использования только Service Layer.

### Изменения в bot.py

**1. Убрать дублирующие импорты:**

До:
```python
from .database import Database
from .models import Room, Booking
from .repository import SQLiteRepository
from .service import RoomBookingService
```

После:
```python
from .repository import SQLiteRepository
from .service import RoomBookingService
```

**2. Убрать прямой доступ к БД:**

До:
```python
def __init__(self, token: str, db_path: str = "bookings.db"):
    self.bot = Bot(token=token)
    self.dp = Dispatcher()
    self.db = Database(db_path)  # ← УБРАТЬ

    self.repository = SQLiteRepository(db_path)
    self.service = RoomBookingService(self.repository)
```

После:
```python
def __init__(self, token: str, db_path: str = "bookings.db"):
    self.bot = Bot(token=token)
    self.dp = Dispatcher()

    # Initialize service layer (single source of truth)
    self.repository = SQLiteRepository(db_path)
    self.service = RoomBookingService(self.repository)
```

**3. Переписать все команды:**

Пример `/available`:

До:
```python
async def cmd_available(self, message: Message):
    rooms = Room.get_all(self.db)
    current_time = datetime.now()  # ← НЕПРАВИЛЬНО! Серверное время

    for room in rooms:
        current_booking = room.get_current_booking(current_time)
        # ...
```

После:
```python
async def cmd_available(self, message: Message):
    result = self.service.list_available_rooms()  # ← Использует self.service.now()

    for room in result['available']:
        # ...
```

Пример `/book`:

До (77 строк):
```python
async def cmd_book(self, message: Message):
    # Парсинг regex
    match = re.match(r'^(.+?)\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$', args[1])

    # Проверка комнаты
    room = Room.get(room_name, self.db)

    # Конвертация времени (НЕПРАВИЛЬНО - серверное время)
    today = datetime.now().date()
    start_time = datetime.strptime(...)

    # Создание бронирования
    booking = Booking.create(...)

    # Проверка конфликта
    conflict = self.db.check_booking_conflict(...)
```

После (35 строк):
```python
async def cmd_book(self, message: Message):
    # Простой парсинг
    parts = args[1].rsplit(maxsplit=1)
    room_name = parts[0].strip()
    time_range = parts[1].strip()

    # Service делает ВСЁ: валидация, timezone, конфликты
    result = self.service.book_room(
        room_name=room_name,
        user_id=message.from_user.id,
        username=message.from_user.full_name,
        time_range=time_range
    )

    await message.answer(result['message'])
```

## Коммит

**Файлы:**
- `src/bot.py` - полный рефакторинг всех команд

**Изменения:**
- Убраны импорты `Database`, `Room`, `Booking`, `re`, `types`
- Убран `self.db` из конструктора
- Все команды переведены на `self.service.*`
- Код сократился с ~466 до ~365 строк

**Коммит:**
```
Refactor bot to use Service Layer exclusively

Problem:
- Bot was bypassing Service Layer, using Database and Models directly
- This caused timezone bugs: datetime.now() instead of self.service.now()
- Duplicate code between bot handlers and service methods

Solution:
- Remove direct database access (self.db)
- Remove unused imports (Database, Room, Booking, re, types)
- Refactor all commands to use self.service methods:
  - /rooms → self.service.list_all_rooms()
  - /available → self.service.list_available_rooms()
  - /book → self.service.book_room()
  - /release → self.service.release_room()
  - /status → self.service.get_room_status()
  - /mybooks → self.service.get_user_bookings()
  - All admin commands → self.service.*

Result:
- Single source of truth for business logic
- Timezone now works correctly in all commands
- Cleaner code (466 → 365 lines)
- All 105 tests still pass

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Итоговая статистика (после Evolution 5)

**Коммиты:**
- MVP: 9
- Эволюции: 11 (Docker + Tests + Admin + Timezone + Service Refactor)
- **Итого: 20**

**Тесты:**
- BDD: 10
- Unit Database: 23 (18 + 5 settings)
- Unit Service: 31
- Unit Admin: 15
- Unit Timezone: 12
- Integration: 14
- **Итого: 105 тестов (все проходят)**

**Архитектура (теперь корректная):**
```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (bot.py - Telegram интерфейс)         │
│  Только парсинг и форматирование       │
└─────────────────┬───────────────────────┘
                  │ self.service.*
┌─────────────────▼───────────────────────┐
│          Service Layer                  │
│  (service.py - ВСЯ бизнес-логика)      │
│  Timezone, валидация, конфликты        │
└─────────────────┬───────────────────────┘
                  │ self.repo.*
┌─────────────────▼───────────────────────┐
│       Repository Interface              │
│  (repository.py - абстракция данных)   │
└──────┬──────────────────────┬───────────┘
       │                      │
┌──────▼────────┐    ┌───────▼──────────┐
│ SQLite Repo   │    │ InMemory Repo    │
│ (production)  │    │ (tests)          │
└───────────────┘    └──────────────────┘
```

## Преимущества рефакторинга

1. **Исправлен баг с таймзоной**: Все команды теперь используют офисное время
2. **Единая точка входа**: Вся логика в Service Layer
3. **Меньше кода**: -100 строк (меньше дублирования)
4. **Тестируемость**: Bot layer тривиален, вся логика протестирована в service
5. **Расширяемость**: Легко добавить CLI/API поверх того же Service

## Что изменилось для пользователей

**Ничего видимого** - все команды работают так же, но теперь:
- `/available` показывает корректный статус с учетом таймзоны
- `/book` бронирует на правильное время
- `/status` показывает правильное время окончания брони

## Lessons Learned

1. **Service Layer с самого начала**: Нужно было сразу проектировать бот через сервис
2. **Не создавать двух путей к данным**: `self.db` и `self.service` - антипаттерн
3. **Timezone везде или нигде**: Нельзя частично внедрять timezone-aware код
4. **Рефакторить раньше**: Технический долг накапливается быстро
