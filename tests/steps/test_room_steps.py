"""Step definitions for room booking BDD tests."""
from datetime import datetime
from pytest_bdd import scenarios, given, when, then, parsers


# Load all feature files
scenarios('../features/list_rooms.feature')
scenarios('../features/view_rooms.feature')
scenarios('../features/book_room.feature')
scenarios('../features/release_room.feature')
scenarios('../features/who_booked.feature')


# ============================================================================
# GIVEN steps (preconditions) - простая подготовка данных
# ============================================================================

@given(parsers.parse('в системе есть следующие переговорки:\n{table}'), target_fixture='rooms_setup')
@given(parsers.parse('в системе есть переговорка "{room_name}"'))
def setup_rooms(test_context, room_name=None, table=None):
    """Setup rooms in the system."""
    # TODO: вызвать database.add_room() когда будет реализовано
    if table:
        lines = table.strip().split('\n')
        for line in lines[1:]:  # Skip header
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                capacity = int(parts[1])
                test_context['rooms'][name] = {'capacity': capacity}
    elif room_name:
        test_context['rooms'][room_name] = {'capacity': 6}
    return test_context


@given(parsers.parse('пользователь "{username}" авторизован'))
def set_current_user(test_context, username):
    """Set current user."""
    test_context['current_user'] = username


@given(parsers.parse('"{room_name}" свободен'))
def room_is_free(test_context, room_name):
    """Ensure room is free (no bookings)."""
    # TODO: вызвать database.clear_bookings(room_name) когда будет реализовано
    pass


@given(parsers.parse('"{room_name}" забронирован с {start_time} до {end_time}'))
@given(parsers.parse('"{room_name}" забронирован пользователем "{username}" с {start_time} до {end_time}'))
@given(parsers.parse('"{room_name}" забронирован "{username}" с {start_time} до {end_time}'))
def room_is_booked(test_context, room_name, start_time, end_time, username=None):
    """Book a room for testing."""
    # TODO: вызвать database.create_booking() когда будет реализовано
    booking_user = username or "TestUser"
    test_context.setdefault('test_bookings', []).append({
        'room': room_name,
        'user': booking_user,
        'start': start_time,
        'end': end_time
    })


@given(parsers.parse('текущее время {current_time}'))
def set_current_time(test_context, current_time):
    """Set current time for testing."""
    hour, minute = map(int, current_time.split(':'))
    test_context['current_time'] = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


@given(parsers.parse('"{room_name}" не забронирован'))
def room_not_booked(test_context, room_name):
    """Ensure room has no bookings."""
    # TODO: вызвать database.clear_bookings(room_name) когда будет реализовано
    pass


# ============================================================================
# WHEN steps (actions) - заглушки для вызовов бота
# ============================================================================

@when(parsers.parse('пользователь вызывает команду "{command}"'))
def user_calls_command(test_context, command):
    """Simulate user calling a bot command."""
    # TODO: вызвать реальный обработчик команды бота
    # Например: bot.handle_command(command, user=test_context['current_user'])
    test_context['last_command'] = command
    test_context['bot_response'] = None
    test_context['available_rooms'] = []
    raise NotImplementedError(f"Bot command handling not implemented yet: {command}")


# ============================================================================
# THEN steps (assertions) - заглушки для проверок
# ============================================================================

@then(parsers.parse('бот показывает {count:d} свободные переговорки'))
@then(parsers.parse('бот показывает {count:d} свободных переговорок'))
def check_available_rooms_count(test_context, count):
    """Check number of available rooms."""
    # TODO: проверить результат работы бота
    raise NotImplementedError(f"Check for {count} available rooms not implemented yet")


@then(parsers.parse('в списке есть "{room1}", "{room2}", "{room3}"'))
@then(parsers.parse('в списке есть "{room1}", "{room2}", "{room3}", "{room4}"'))
def check_rooms_in_list(test_context, room1, room2, room3, room4=None):
    """Check that specific rooms are in the list."""
    # TODO: проверить что комнаты в списке ответа бота
    rooms = [room1, room2, room3]
    if room4:
        rooms.append(room4)
    raise NotImplementedError(f"Check for rooms {rooms} in list not implemented yet")


@then(parsers.parse('"{room_name}" помечен как занятый до {end_time}'))
def check_room_marked_busy(test_context, room_name, end_time):
    """Check that room is marked as busy."""
    # TODO: проверить что комната помечена как занятая в ответе бота
    raise NotImplementedError(f"Check for {room_name} marked as busy until {end_time} not implemented yet")


@then(parsers.parse('бот показывает список из {count:d} переговорок'))
def check_total_rooms_count(test_context, count):
    """Check total number of rooms in list."""
    # TODO: проверить количество комнат в ответе бота
    raise NotImplementedError(f"Check for total {count} rooms not implemented yet")


@then(parsers.parse('бронирование создается на имя "{username}"'))
def check_booking_created(test_context, username):
    """Check that booking was created for user."""
    # TODO: проверить что бронирование создано через database.get_booking()
    raise NotImplementedError(f"Check booking created for {username} not implemented yet")


@then(parsers.parse('бронирование не создается'))
def check_booking_not_created(test_context):
    """Check that booking was not created."""
    # TODO: проверить что бронирование НЕ создано
    raise NotImplementedError("Check booking not created - not implemented yet")


@then(parsers.parse('бронирование удаляется'))
def check_booking_deleted(test_context):
    """Check that booking was deleted."""
    # TODO: проверить что бронирование удалено
    raise NotImplementedError("Check booking deleted - not implemented yet")


@then(parsers.parse('бронирование не удаляется'))
def check_booking_not_deleted(test_context):
    """Check that booking was not deleted."""
    # TODO: проверить что бронирование НЕ удалено
    raise NotImplementedError("Check booking not deleted - not implemented yet")


@then(parsers.parse('бот отвечает "{expected_response}"'))
def check_bot_response(test_context, expected_response):
    """Check bot response message."""
    # TODO: проверить ответ бота
    raise NotImplementedError(f"Check bot response '{expected_response}' - not implemented yet")
