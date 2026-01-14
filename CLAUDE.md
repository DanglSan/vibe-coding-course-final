# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Это экзаменационный проект для курса **Vibe Coding 2025** (ИТМО, магистратура).

**Цель**: Создать работающий MVP одного из 20 проектов с использованием BDD-подхода и AI как соавтора.

## Критерии оценки (25 баллов)

1. **Работоспособность MVP** (2-5 баллов) - запускается и решает заявленную проблему
2. **Эволюция коммитов** (2-5 баллов) - 10+ осмысленных коммитов, видно развитие
3. **Тесты** (2-5 баллов) - pytest-bdd с .feature файлами, тесты ДО кода
4. **Документация** (2-5 баллов) - README + CLAUDE.md + инструкция по запуску
5. **Vibe Coding подход** (2-5 баллов) - BDD как спецификация, AI как соавтор

## Development Workflow

### 1. BDD-First Approach

**КРИТИЧЕСКИ ВАЖНО**: Тесты пишутся ДО кода!

```bash
# Структура тестов
tests/
├── features/          # BDD .feature файлы (Gherkin)
└── steps/            # Step definitions (pytest-bdd)
```

**Порядок работы**:
1. Написать .feature файл с BDD-сценарием (Gherkin)
2. Создать step definitions для pytest-bdd
3. Убедиться что тест падает (Red)
4. Написать код для прохождения теста (Green)
5. Отрефакторить при необходимости (Refactor)

### 2. Running Tests

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск всех тестов
pytest

# Запуск с выводом BDD-сценариев
pytest --gherkin-terminal-reporter

# Запуск конкретного .feature файла
pytest tests/features/имя_файла.feature
```

### 3. Common Commands

```bash
# Установка зависимостей для разработки
pip install pytest pytest-bdd

# Для Telegram ботов
pip install aiogram

# Для CLI приложений
pip install click
```

## Project Structure

```
project-root/
├── README.md           # Описание проекта + инструкция по запуску
├── CLAUDE.md           # Этот файл
├── requirements.txt    # Python зависимости
├── src/
│   └── ...            # Исходный код приложения
├── tests/
│   ├── features/      # BDD .feature файлы (Gherkin)
│   └── steps/         # Step definitions (pytest-bdd)
└── .gitignore
```

## Git Workflow

**Важно**: Делать частые, осмысленные коммиты (10+ за проект)

Коммиты должны показывать эволюцию проекта:
- Не коммитить весь код сразу
- Коммитить после каждого завершенного сценария
- Коммитить после реализации каждой фичи
- Сообщения коммитов должны быть понятными

Пример хорошей истории коммитов:
```
1. Add initial BDD scenarios for booking rooms
2. Implement step definitions for room booking
3. Add room availability checker
4. Add SQLite database schema
5. Implement booking storage
6. Add tests for booking conflicts
7. Implement conflict detection
8. Add user notification feature
9. Add README with setup instructions
10. Add CLAUDE.md documentation
```

## Technology Stack Recommendations

В зависимости от выбранного проекта:

**Для Telegram ботов**:
- `aiogram` - асинхронная библиотека для Telegram Bot API
- `SQLite` - локальная БД
- `APScheduler` - для напоминаний и периодических задач

**Для CLI приложений**:
- `click` - создание CLI интерфейса
- `SQLite` - хранение данных
- `datetime/pytz` - работа с датами

## BDD Examples

### Пример .feature файла:

```gherkin
Feature: Бронирование переговорок
  Как сотрудник офиса
  Я хочу бронировать переговорки через бота
  Чтобы не искать свободные комнаты вручную

  Scenario: Просмотр свободных переговорок
    Given в базе есть 3 переговорки
    And переговорка "Марс" занята с 14:00 до 15:00
    When пользователь спрашивает "свободна?"
    Then бот показывает 2 свободные переговорки
    And "Марс" отмечена как занятая до 15:00

  Scenario: Бронирование свободной переговорки
    Given переговорка "Венера" свободна
    When пользователь пишет "бронь Венера 15:00-16:00"
    Then бот создает бронь на имя пользователя
    And бот подтверждает бронирование
```

## Working with Claude

При работе с Claude Code:
- Показывать .feature файлы для генерации step definitions
- Просить сгенерировать код для прохождения тестов
- Делать коммиты после каждой завершенной фичи
- Просить улучшить документацию по ходу разработки

## Testing Philosophy

**Тесты - это спецификация**, а не просто проверка кода:
- BDD-сценарии описывают поведение системы на языке бизнеса
- Каждая фича должна быть покрыта тестами
- Тесты пишутся ДО кода (Test-First)
- Тесты должны быть читаемыми и понятными

## Delivery Checklist

Перед отправкой проекта проверить:
- [ ] Репозиторий на GitHub
- [ ] README с описанием и инструкцией запуска
- [ ] CLAUDE.md с описанием работы с AI
- [ ] BDD .feature файлы (pytest-bdd)
- [ ] Тесты запускаются и проходят
- [ ] 10+ коммитов с понятными сообщениями
- [ ] MVP работает и решает проблему заказчика
