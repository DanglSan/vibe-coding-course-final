# Evolution 4: Timezone Management (Управление таймзоной)

## Проблема

Бот использует серверное время (`datetime.now()`), которое может не совпадать с местным временем офиса:
- Сервер в UTC, офис в MSK (UTC+3)
- Пользователи вводят время в своей таймзоне: "15:00-16:00"
- Бот сохраняет в серверной таймзоне → конфликты и путаница

## Решение

Добавить команду `/admin_set_timezone <offset>` для установки офисной таймзоны.

**Примеры:**
- `/admin_set_timezone +3` - Москва (MSK)
- `/admin_set_timezone +5` - Екатеринбург
- `/admin_set_timezone -5` - Нью-Йорк (EST)

## Архитектура изменений

### 1. Database Layer

**Новая таблица `settings`:**
```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

**Новые методы в database.py:**
```python
def set_setting(self, key: str, value: str) -> None
def get_setting(self, key: str, default: str = None) -> Optional[str]
```

### 2. Repository Layer

**Новые методы в repository.py (интерфейс):**
```python
@abstractmethod
def set_setting(self, key: str, value: str) -> None

@abstractmethod
def get_setting(self, key: str, default: str = None) -> Optional[str]
```

**Реализация в SQLiteRepository:**
```python
def set_setting(self, key: str, value: str) -> None:
    self.db.set_setting(key, value)

def get_setting(self, key: str, default: str = None) -> Optional[str]:
    return self.db.get_setting(key, default)
```

**Реализация в InMemoryRepository:**
```python
def __init__(self):
    # ... existing code ...
    self.settings: Dict[str, str] = {}

def set_setting(self, key: str, value: str) -> None:
    self.settings[key] = value

def get_setting(self, key: str, default: str = None) -> Optional[str]:
    return self.settings.get(key, default)
```

### 3. Service Layer

**Новый класс TimezoneMixin в service.py:**
```python
from datetime import timezone, timedelta

class TimezoneMixin:
    """Mixin for timezone-aware datetime operations."""

    def get_timezone(self) -> timezone:
        """Get configured timezone from settings."""
        offset_str = self.repo.get_setting('timezone_offset', '+0')
        offset_hours = int(offset_str)
        return timezone(timedelta(hours=offset_hours))

    def now(self) -> datetime:
        """Get current time in configured timezone."""
        return datetime.now(self.get_timezone())

    def parse_time_to_timezone(self, time_str: str) -> datetime:
        """Parse time string (HH:MM) to timezone-aware datetime."""
        # Parse HH:MM
        # Get today's date in timezone
        # Combine and return timezone-aware datetime
```

**Обновить RoomBookingService:**
```python
class RoomBookingService(TimezoneMixin):
    # Заменить все datetime.now() на self.now()
    # Обновить _parse_time_range для работы с timezone
```

**Новые методы:**
```python
def set_timezone(self, offset: int) -> Dict[str, Any]:
    """Admin: set timezone offset.

    Args:
        offset: Timezone offset in hours (-12 to +14)

    Returns:
        {'success': bool, 'message': str}
    """
    if not (-12 <= offset <= 14):
        return {
            'success': False,
            'message': '❌ Смещение должно быть от -12 до +14 часов'
        }

    offset_str = f"{offset:+d}"  # "+3" or "-5"
    self.repo.set_setting('timezone_offset', offset_str)

    return {
        'success': True,
        'message': f'✅ Таймзона установлена: UTC{offset_str}'
    }

def get_current_timezone(self) -> Dict[str, Any]:
    """Get current timezone setting."""
    offset_str = self.repo.get_setting('timezone_offset', '+0')
    return {
        'offset': offset_str,
        'display': f'UTC{offset_str}'
    }
```

### 4. Bot Layer

**Новая команда в bot.py:**
```python
async def cmd_admin_set_timezone(self, message: Message):
    """Admin: set timezone - /admin_set_timezone <offset>"""
    if not self._check_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        # Show current timezone
        tz_info = self.service.get_current_timezone()
        await message.answer(
            f"🌍 Текущая таймзона: {tz_info['display']}\n\n"
            f"Использование: /admin_set_timezone <смещение>\n"
            f"Примеры:\n"
            f"  /admin_set_timezone +3  (Москва)\n"
            f"  /admin_set_timezone +5  (Екатеринбург)\n"
            f"  /admin_set_timezone -5  (Нью-Йорк)"
        )
        return

    try:
        offset = int(args[1])
    except ValueError:
        await message.answer("❌ Смещение должно быть числом (например: +3 или -5)")
        return

    result = self.service.set_timezone(offset)
    await message.answer(result['message'])
```

**Обновить /start для админов:**
```python
if is_admin:
    welcome_text += (
        "\n\n👑 Команды администратора:\n"
        # ... existing commands ...
        "/admin_set_timezone <offset> - установить таймзону\n"
    )
```

## Коммиты (3 коммита)

### Commit 1: Add settings table and timezone infrastructure

**Файлы:**
- `src/database.py` - таблица settings + 2 метода
- `src/repository.py` - интерфейс + реализации (SQLite + InMemory)
- `tests/unit/test_database.py` - тесты для settings (5 тестов)

**Тесты:**
```python
class TestSettingsOperations:
    def test_set_and_get_setting(self, temp_db)
    def test_get_nonexistent_setting_returns_none(self, temp_db)
    def test_get_nonexistent_setting_with_default(self, temp_db)
    def test_update_existing_setting(self, temp_db)
    def test_settings_persistence(self, temp_db)
```

**Коммит:**
```
Add settings table for configuration storage

- Create settings table in database schema
- Add set_setting and get_setting methods to Database layer
- Add settings interface to Repository pattern
- Implement settings in SQLite and InMemory repositories
- Add 5 unit tests for settings operations

Prepares infrastructure for timezone management

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Commit 2: Add timezone management in service layer

**Файлы:**
- `src/service.py` - TimezoneMixin + методы set_timezone, get_current_timezone
- `tests/unit/test_timezone_service.py` - новый файл с тестами (12 тестов)

**Тесты:**
```python
class TestTimezoneManagement:
    def test_set_timezone_positive_offset(self, service)
    def test_set_timezone_negative_offset(self, service)
    def test_set_timezone_invalid_offset_too_large(self, service)
    def test_set_timezone_invalid_offset_too_small(self, service)
    def test_get_current_timezone_default(self, service)
    def test_get_current_timezone_after_set(self, service)

class TestTimezoneAwareDatetime:
    def test_now_returns_timezone_aware(self, service)
    def test_now_respects_configured_timezone(self, service)
    def test_parse_time_range_with_timezone(self, service)
    def test_booking_uses_configured_timezone(self, service)
    def test_availability_check_uses_timezone(self, service)
    def test_multiple_timezones(self, service)
```

**Коммит:**
```
Add timezone management to service layer

- Add TimezoneMixin for timezone-aware datetime operations
- Add set_timezone and get_current_timezone methods
- Update RoomBookingService to use configured timezone
- Replace all datetime.now() with timezone-aware self.now()
- Update _parse_time_range to work with timezones
- Add 12 unit tests for timezone functionality

Bookings now respect configured office timezone

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Commit 3: Add admin timezone command and documentation

**Файлы:**
- `src/bot.py` - команда /admin_set_timezone
- `README.md` - документация команды
- `CLAUDE.md` - Evolution 4
- `exam-process/03-timezone-evolution-plan.md` - этот файл
- `exam-process/README.md` - обновить статус

**README.md изменения:**

В секции "Административные команды" добавить:

```markdown
#### `/admin_set_timezone <offset>`
Установить таймзону офиса для корректного отображения времени

**Использование:**
```
/admin_set_timezone +3
✅ Таймзона установлена: UTC+3
```

**Примеры смещений:**
- `+3` - Москва (MSK)
- `+5` - Екатеринбург (YEKT)
- `+7` - Красноярск (KRAT)
- `-5` - Нью-Йорк (EST)
- `-8` - Лос-Анджелес (PST)

**Просмотр текущей таймзоны:**
```
/admin_set_timezone
🌍 Текущая таймзона: UTC+3
```

**Важно:** Все бронирования используют установленную таймзону. Пользователи вводят время в местном времени офиса.
```

**CLAUDE.md изменения:**

Добавить в секцию "Эволюции проекта":

```markdown
#### Evolution 4: Timezone Management 🌍

**Цель**: Поддержка разных часовых поясов для корректной работы бронирований

**Реализовано:**
- Таблица `settings` в БД для хранения конфигурации
- TimezoneMixin в Service Layer для timezone-aware операций
- Команда `/admin_set_timezone <offset>` для настройки таймзоны
- Все операции с временем используют настроенную таймзону
- 17 новых тестов (5 database + 12 service)

**Результат**: Бот корректно работает в любой таймзоне, установленной администратором
```

**exam-process/README.md обновить:**

```markdown
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
**Проверка всех тестов**: `pytest -v` → 105 passed
```

**Коммит:**
```
Add admin timezone command and update documentation

Bot changes:
- Add /admin_set_timezone <offset> command for admins
- Update /start to show timezone command for admins
- Display current timezone when command called without arguments

Documentation updates:
- README.md: Add timezone command with examples for different cities
- CLAUDE.md: Add Evolution 4 documentation
- exam-process/03-timezone-evolution-plan.md: Create detailed plan
- exam-process/README.md: Update evolution status (19 commits, 105 tests)

All bookings now use configured timezone instead of server time

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Итоговая статистика (после Evolution 4)

**Коммиты:**
- MVP: 9
- Эволюции: 10 (Docker + Tests + Admin + Timezone)
- **Итого: 19**

**Тесты:**
- BDD: 10
- Unit Database: 18 + 5 (settings) = 23
- Unit Service: 31
- Unit Admin: 15
- Unit Timezone: 12
- Integration: 14
- **Итого: 105 тестов**

**Функционал:**
- Пользовательские команды: 7
- Административные команды: 6 (добавлена timezone)
- **Итого: 13 команд**

## Технические детали

### Как работает timezone-aware datetime

**До (проблема):**
```python
# Серверное время (UTC)
datetime.now()  # 2026-01-14 12:00:00 (UTC)

# Пользователь в Москве вводит
"/book Марс 15:00-16:00"  # Ожидает 15:00 MSK

# Бот сохраняет как
start_time = datetime(2026, 1, 14, 15, 0)  # Но это 15:00 UTC!
# Реально забронировано на 18:00 MSK - НЕПРАВИЛЬНО!
```

**После (решение):**
```python
# Настроенная таймзона (MSK = UTC+3)
tz = timezone(timedelta(hours=3))
datetime.now(tz)  # 2026-01-14 15:00:00+03:00

# Пользователь в Москве вводит
"/book Марс 15:00-16:00"

# Бот парсит с учетом таймзоны
start_time = datetime(2026, 1, 14, 15, 0, tzinfo=tz)
# Сохраняет: 2026-01-14 15:00:00+03:00
# Это корректное время - 15:00 MSK!
```

### Пример использования

**Администратор настраивает таймзону:**
```
Admin: /admin_set_timezone +3
Bot: ✅ Таймзона установлена: UTC+3
```

**Пользователь бронирует:**
```
User: /book Марс 15:00-16:00
Bot: ✅ Марс забронирован на 15:00-16:00

# Под капотом:
# - Время парсится как 15:00 MSK (UTC+3)
# - Сохраняется как 2026-01-14T15:00:00+03:00
# - Конвертируется в UTC для БД: 2026-01-14T12:00:00+00:00
# - При отображении конвертируется обратно в MSK: 15:00
```

**Проверка доступности:**
```
User: /available
# Текущее время в MSK: 14:30
# Проверяет бронирования с учетом MSK
Bot: 🔴 Занятые переговорки:
     • Марс - занят до 16:00
```

## Преимущества решения

1. **Корректность**: Все операции с временем в одной таймзоне
2. **Гибкость**: Можно переключать таймзону без изменения кода
3. **Тестируемость**: Легко тестировать с разными таймзонами
4. **Расширяемость**: Можно добавить per-user таймзоны в будущем

## Альтернативные подходы (не выбраны)

### Подход 1: Хранить offset в каждом booking
**Минусы:**
- Избыточность (одно и то же значение в каждой записи)
- Сложно изменить таймзону для существующих броней

### Подход 2: Использовать pytz
**Минусы:**
- Дополнительная зависимость
- Избыточная сложность (нам нужен только offset)
- Проблемы с DST (daylight saving time)

### Подход 3: Конвертировать в UTC при сохранении
**Минусы:**
- Потеря информации о "местном времени"
- Сложность при смене таймзоны

## Следующие шаги (опционально)

1. **DST Support**: Автоматическое переключение летнего/зимнего времени
2. **Per-User Timezones**: Каждый пользователь в своей таймзоне
3. **Named Timezones**: "Europe/Moscow" вместо "+3"
4. **Timezone Validation**: Проверка корректности offset при установке
