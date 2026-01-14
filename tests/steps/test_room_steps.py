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
# GIVEN steps (preconditions) - подготовка данных через Repository
# ============================================================================

@given(parsers.parse('в системе есть следующие переговорки:\n{table}'))
def setup_multiple_rooms(test_context, table):
    """Setup multiple rooms from table."""
    repo = test_context['repository']

    lines = table.strip().split('\n')
    for line in lines[1:]:  # Skip header
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 2:
            name = parts[0]
            capacity = int(parts[1])
            repo.add_room(name, capacity)
            test_context['rooms'][name] = {'capacity': capacity}


@given(parsers.parse('в системе есть переговорка "{room_name}"'))
def setup_single_room(test_context, room_name):
    """Setup a single room."""
    repo = test_context['repository']
    repo.add_room(room_name, 6)
    test_context['rooms'][room_name] = {'capacity': 6}


@given(parsers.parse('пользователь "{username}" авторизован'))
def set_current_user(test_context, username):
    """Set current user."""
    test_context['current_user'] = username
    # Используем разные ID для разных пользователей
    if username == "Вася":
        test_context['current_user_id'] = 12345
    elif username == "Петя":
        test_context['current_user_id'] = 67890
    else:
        test_context['current_user_id'] = 99999


@given(parsers.parse('"{room_name}" свободен'))
def room_is_free(test_context, room_name):
    """Ensure room is free (no bookings)."""
    repo = test_context['repository']
    repo.delete_room_bookings(room_name)


@given(parsers.parse('"{room_name}" забронирован с {start_time} до {end_time}'))
def room_is_booked_simple(test_context, room_name, start_time, end_time):
    """Book a room with current user or TestUser."""
    repo = test_context['repository']
    booking_user = test_context.get('current_user', 'TestUser')

    # Конвертируем время в ISO формат
    today = datetime.now().date()
    start_dt = datetime.strptime(f"{today} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{today} {end_time}", "%Y-%m-%d %H:%M")

    # Определяем user_id
    if booking_user == "Вася":
        user_id = 12345
    elif booking_user == "Петя":
        user_id = 67890
    else:
        user_id = 99999

    booking_id = repo.create_booking(
        room_name=room_name,
        user_id=user_id,
        username=booking_user,
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat()
    )
    test_context['last_booking_id'] = booking_id


@given(parsers.parse('"{room_name}" забронирован пользователем "{username}" с {start_time} до {end_time}'))
def room_is_booked_by_user(test_context, room_name, username, start_time, end_time):
    """Book a room by specific user."""
    repo = test_context['repository']

    # Конвертируем время в ISO формат
    today = datetime.now().date()
    start_dt = datetime.strptime(f"{today} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{today} {end_time}", "%Y-%m-%d %H:%M")

    # Определяем user_id
    if username == "Вася":
        user_id = 12345
    elif username == "Петя":
        user_id = 67890
    else:
        user_id = 99999

    booking_id = repo.create_booking(
        room_name=room_name,
        user_id=user_id,
        username=username,
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat()
    )
    test_context['last_booking_id'] = booking_id


@given(parsers.parse('текущее время {current_time}'))
def set_current_time(test_context, current_time):
    """Set current time for testing."""
    hour, minute = map(int, current_time.split(':'))
    test_context['current_time'] = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


@given(parsers.parse('"{room_name}" не забронирован'))
def room_not_booked(test_context, room_name):
    """Ensure room has no bookings."""
    repo = test_context['repository']
    repo.delete_room_bookings(room_name)


# ============================================================================
# WHEN steps (actions) - вызов Service Layer через команды
# ============================================================================

@when(parsers.parse('пользователь вызывает команду "{command}"'))
def user_calls_command(test_context, command):
    """Simulate user calling a bot command with arguments."""
    service = test_context['service']
    user_id = test_context.get('current_user_id', 12345)
    username = test_context.get('current_user', 'TestUser')
    current_time = test_context.get('current_time', datetime.now())

    test_context['last_command'] = command

    # Parse command and arguments
    parts = command.split(maxsplit=1)
    cmd = parts[0]
    args = parts[1] if len(parts) > 1 else None

    if cmd == "/rooms":
        # List all rooms
        rooms = service.list_all_rooms()
        test_context['available_rooms'] = rooms
        test_context['bot_response'] = f"Найдено комнат: {len(rooms)}"

    elif cmd == "/available":
        # List available rooms
        result = service.list_available_rooms(current_time)
        test_context['available_rooms'] = result['available']
        test_context['occupied_info'] = result['occupied']

    elif cmd == "/book":
        # Book a room: /book <room_name> <time_range>
        if args:
            # Parse: "Марс 15:00-16:00"
            import re
            match = re.match(r'^(.+?)\s+(\d{1,2}:\d{2}-\d{1,2}:\d{2})$', args)
            if match:
                room_name = match.group(1)
                time_range = match.group(2)
                result = service.book_room(room_name, user_id, username, time_range)
                test_context['booking_created'] = result['success']
                test_context['last_booking_id'] = result['booking_id']
                test_context['bot_response'] = result['message']
            else:
                test_context['bot_response'] = "❌ Неверный формат команды /book"
        else:
            test_context['bot_response'] = "❌ Укажите переговорку и время"

    elif cmd == "/release":
        # Release a room: /release <room_name>
        if args:
            room_name = args.strip()
            result = service.release_room(room_name, user_id)
            test_context['booking_deleted'] = result['success']
            test_context['bot_response'] = result['message']
        else:
            test_context['bot_response'] = "❌ Укажите переговорку"

    elif cmd == "/status":
        # Get room status: /status <room_name>
        if args:
            room_name = args.strip()
            result = service.get_room_status(room_name, current_time)
            test_context['bot_response'] = result['message']
        else:
            test_context['bot_response'] = "❌ Укажите переговорку"

    else:
        test_context['bot_response'] = f"Unknown command: {command}"


# ============================================================================
# THEN steps (assertions) - проверка результатов
# ============================================================================

@then(parsers.parse('бот показывает {count:d} свободные переговорки'))
@then(parsers.parse('бот показывает {count:d} свободных переговорок'))
def check_available_rooms_count(test_context, count):
    """Check number of available rooms."""
    available_rooms = test_context.get('available_rooms', [])
    assert len(available_rooms) == count, (
        f"Expected {count} available rooms, got {len(available_rooms)}"
    )


@then(parsers.parse('в списке есть "{room1}", "{room2}"'))
@then(parsers.parse('в списке есть "{room1}", "{room2}", "{room3}"'))
@then(parsers.parse('в списке есть "{room1}", "{room2}", "{room3}", "{room4}"'))
def check_rooms_in_list(test_context, room1, room2, room3=None, room4=None):
    """Check that specific rooms are in the list."""
    available_rooms = test_context.get('available_rooms', [])
    room_names = [r['name'] for r in available_rooms]

    expected_rooms = [room1, room2]
    if room3:
        expected_rooms.append(room3)
    if room4:
        expected_rooms.append(room4)

    for expected_room in expected_rooms:
        assert expected_room in room_names, (
            f"Room '{expected_room}' not found in available rooms: {room_names}"
        )


@then(parsers.parse('"{room_name}" помечен как занятый до {end_time}'))
def check_room_marked_busy(test_context, room_name, end_time):
    """Check that room is marked as busy."""
    occupied_info = test_context.get('occupied_info', {})
    assert room_name in occupied_info, f"Room '{room_name}' not marked as busy"
    assert occupied_info[room_name] == end_time, (
        f"Expected {room_name} busy until {end_time}, "
        f"got {occupied_info[room_name]}"
    )


@then(parsers.parse('бот показывает список из {count:d} переговорок'))
def check_total_rooms_count(test_context, count):
    """Check total number of rooms in list."""
    available_rooms = test_context.get('available_rooms', [])
    assert len(available_rooms) == count, (
        f"Expected {count} total rooms, got {len(available_rooms)}"
    )


@then(parsers.parse('бронирование создается на имя "{username}"'))
def check_booking_created(test_context, username):
    """Check that booking was created for user."""
    assert test_context.get('booking_created') is True, "Booking was not created"

    booking_id = test_context.get('last_booking_id')
    assert booking_id is not None, "No booking ID found"

    repo = test_context['repository']
    booking_data = repo.get_booking(booking_id)
    assert booking_data is not None, f"Booking {booking_id} not found in repository"
    assert booking_data['username'] == username, (
        f"Expected booking for {username}, got {booking_data['username']}"
    )


@then(parsers.parse('бронирование не создается'))
def check_booking_not_created(test_context):
    """Check that booking was not created."""
    assert test_context.get('booking_created') is False, (
        "Booking should not have been created"
    )


@then(parsers.parse('бронирование удаляется'))
def check_booking_deleted(test_context):
    """Check that booking was deleted."""
    assert test_context.get('booking_deleted') is True, "Booking was not deleted"


@then(parsers.parse('бронирование не удаляется'))
def check_booking_not_deleted(test_context):
    """Check that booking was not deleted."""
    assert test_context.get('booking_deleted') is False, (
        "Booking should not have been deleted"
    )


@then(parsers.parse('бот отвечает "{expected_response}"'))
def check_bot_response(test_context, expected_response):
    """Check bot response message."""
    bot_response = test_context.get('bot_response', '')
    assert expected_response in bot_response, (
        f"Expected response to contain '{expected_response}', "
        f"got: '{bot_response}'"
    )
