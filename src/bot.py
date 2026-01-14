"""Telegram bot for room booking system."""
import os
import re
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from .database import Database
from .models import Room, Booking
from .repository import SQLiteRepository
from .service import RoomBookingService

# Load environment variables
load_dotenv()


class RoomBookingBot:
    """Telegram bot for managing room bookings."""

    def __init__(self, token: str, db_path: str = "bookings.db"):
        """Initialize bot."""
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.db = Database(db_path)

        # Initialize service layer for advanced features
        self.repository = SQLiteRepository(db_path)
        self.service = RoomBookingService(self.repository)

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register command handlers."""
        self.dp.message(Command("start"))(self.cmd_start)
        self.dp.message(Command("rooms"))(self.cmd_rooms)
        self.dp.message(Command("available"))(self.cmd_available)
        self.dp.message(Command("book"))(self.cmd_book)
        self.dp.message(Command("release"))(self.cmd_release)
        self.dp.message(Command("status"))(self.cmd_status)
        self.dp.message(Command("mybooks"))(self.cmd_mybooks)
        # Admin commands
        self.dp.message(Command("admin_add_room"))(self.cmd_admin_add_room)
        self.dp.message(Command("admin_delete_room"))(self.cmd_admin_delete_room)
        self.dp.message(Command("admin_add"))(self.cmd_admin_add)
        self.dp.message(Command("admin_remove"))(self.cmd_admin_remove)
        self.dp.message(Command("admin_list"))(self.cmd_admin_list)
        self.dp.message(Command("admin_set_timezone"))(self.cmd_admin_set_timezone)

    async def cmd_start(self, message: Message):
        """Handle /start command."""
        user_id = message.from_user.id
        is_admin = self.db.is_admin(user_id)

        welcome_text = (
            "👋 Привет! Я помогу забронировать переговорку.\n\n"
            "Доступные команды:\n"
            "/rooms - список всех переговорок\n"
            "/available - свободные переговорки сейчас\n"
            "/book <название> <время> - забронировать\n"
            "  Пример: /book Марс 15:00-16:00\n"
            "/release <название> - освободить раньше времени\n"
            "/status <название> - кто занял переговорку\n"
            "/mybooks - мои бронирования"
        )

        if is_admin:
            welcome_text += (
                "\n\n👑 Команды администратора:\n"
                "/admin_add_room <название> <вместимость> - добавить переговорку\n"
                "/admin_delete_room <название> - удалить переговорку\n"
                "/admin_add - добавить админа (ответить на сообщение)\n"
                "/admin_remove - удалить админа (ответить на сообщение)\n"
                "/admin_list - список всех админов\n"
                "/admin_set_timezone <offset> - установить таймзону офиса"
            )

        await message.answer(welcome_text)

    async def cmd_rooms(self, message: Message):
        """Handle /rooms command - list all rooms."""
        rooms = Room.get_all(self.db)

        if not rooms:
            await message.answer("❌ Переговорки не найдены")
            return

        text = "📋 Все переговорки:\n\n"
        for room in rooms:
            text += f"• {room.name} (вместимость: {room.capacity})\n"

        await message.answer(text)

    async def cmd_available(self, message: Message):
        """Handle /available command - list available rooms."""
        rooms = Room.get_all(self.db)
        current_time = datetime.now()

        available_rooms = []
        occupied_rooms = []

        for room in rooms:
            current_booking = room.get_current_booking(current_time)
            if current_booking:
                end_time = current_booking.get_end_time_formatted()
                occupied_rooms.append(f"• {room.name} - занят до {end_time}")
            else:
                available_rooms.append(f"• {room.name} (вместимость: {room.capacity})")

        text = "🟢 Свободные переговорки:\n\n"

        if available_rooms:
            text += "\n".join(available_rooms)
        else:
            text += "Нет свободных переговорок"

        if occupied_rooms:
            text += "\n\n🔴 Занятые переговорки:\n\n"
            text += "\n".join(occupied_rooms)

        await message.answer(text)

    async def cmd_book(self, message: Message):
        """Handle /book command - create booking."""
        # Parse command: /book <room_name> <start>-<end>
        # Example: /book Марс 15:00-16:00
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer(
                "❌ Неверный формат. Используйте:\n"
                "/book <название> <время>\n"
                "Пример: /book Марс 15:00-16:00"
            )
            return

        # Parse room name and time
        match = re.match(r'^(.+?)\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$', args[1])
        if not match:
            await message.answer(
                "❌ Неверный формат времени. Используйте:\n"
                "/book <название> <время>\n"
                "Пример: /book Марс 15:00-16:00"
            )
            return

        room_name = match.group(1).strip()
        start_time_str = match.group(2)
        end_time_str = match.group(3)

        # Check if room exists
        room = Room.get(room_name, self.db)
        if not room:
            await message.answer(f"❌ Переговорка '{room_name}' не найдена")
            return

        # Convert time to ISO format
        today = datetime.now().date()
        try:
            start_time = datetime.strptime(f"{today} {start_time_str}", "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(f"{today} {end_time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            await message.answer("❌ Неверный формат времени")
            return

        if start_time >= end_time:
            await message.answer("❌ Время начала должно быть раньше времени окончания")
            return

        # Create booking
        booking = Booking.create(
            room_name=room_name,
            user_id=message.from_user.id,
            username=message.from_user.full_name,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            db=self.db
        )

        if booking:
            await message.answer(
                f"✅ {room_name} забронирован на {start_time_str}-{end_time_str}"
            )
        else:
            # Check what's the conflict
            conflict = self.db.check_booking_conflict(
                room_name,
                start_time.isoformat(),
                end_time.isoformat()
            )
            if conflict:
                conflict_start = datetime.fromisoformat(conflict['start_time'])
                conflict_end = datetime.fromisoformat(conflict['end_time'])
                await message.answer(
                    f"❌ {room_name} занят с {conflict_start.strftime('%H:%M')} "
                    f"до {conflict_end.strftime('%H:%M')}"
                )
            else:
                await message.answer(f"❌ Не удалось забронировать {room_name}")

    async def cmd_release(self, message: Message):
        """Handle /release command - release booking early."""
        # Parse command: /release <room_name>
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer(
                "❌ Неверный формат. Используйте:\n"
                "/release <название>\n"
                "Пример: /release Марс"
            )
            return

        room_name = args[1].strip()

        # Check if room exists
        room = Room.get(room_name, self.db)
        if not room:
            await message.answer(f"❌ Переговорка '{room_name}' не найдена")
            return

        # Find user's booking for this room
        booking = self.db.find_booking_by_room_and_user(
            room_name,
            message.from_user.id
        )

        if not booking:
            await message.answer(f"❌ У вас нет активной брони для {room_name}")
            return

        # Delete booking
        success = self.db.delete_booking(booking['id'])
        if success:
            await message.answer(f"✅ {room_name} освобожден")
        else:
            await message.answer(f"❌ Не удалось освободить {room_name}")

    async def cmd_status(self, message: Message):
        """Handle /status command - check room status."""
        # Parse command: /status <room_name>
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer(
                "❌ Неверный формат. Используйте:\n"
                "/status <название>\n"
                "Пример: /status Марс"
            )
            return

        room_name = args[1].strip()

        # Check if room exists
        room = Room.get(room_name, self.db)
        if not room:
            await message.answer(f"❌ Переговорка '{room_name}' не найдена")
            return

        # Check current booking
        current_booking = room.get_current_booking(datetime.now())

        if current_booking:
            end_time = current_booking.get_end_time_formatted()
            await message.answer(
                f"{room_name}: {current_booking.username}, до {end_time}"
            )
        else:
            await message.answer(f"{room_name} свободен")

    async def cmd_mybooks(self, message: Message):
        """Handle /mybooks command - show user's bookings."""
        bookings = Booking.get_user_bookings(message.from_user.id, self.db)

        if not bookings:
            await message.answer("У вас нет активных бронирований")
            return

        text = "📅 Ваши бронирования:\n\n"
        for booking in bookings:
            start = datetime.fromisoformat(booking.start_time)
            end = datetime.fromisoformat(booking.end_time)
            text += (
                f"• {booking.room_name}\n"
                f"  {start.strftime('%d.%m.%Y %H:%M')} - "
                f"{end.strftime('%H:%M')}\n\n"
            )

        await message.answer(text)

    # ========================================================================
    # Admin commands
    # ========================================================================

    def _check_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return self.db.is_admin(user_id)

    async def cmd_admin_add_room(self, message: Message):
        """Admin: add new room - /admin_add_room <name> <capacity>"""
        if not self._check_admin(message.from_user.id):
            await message.answer("❌ Эта команда доступна только администраторам")
            return

        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            await message.answer("❌ Использование: /admin_add_room <название> <вместимость>")
            return

        room_name = args[1]
        try:
            capacity = int(args[2])
        except ValueError:
            await message.answer("❌ Вместимость должна быть числом")
            return

        # Check if room already exists
        existing = self.db.get_room(room_name)
        if existing:
            await message.answer(f"❌ Переговорка '{room_name}' уже существует")
            return

        self.db.add_room(room_name, capacity)
        await message.answer(f"✅ Переговорка '{room_name}' (вместимость: {capacity}) добавлена")

    async def cmd_admin_delete_room(self, message: Message):
        """Admin: delete room - /admin_delete_room <name>"""
        if not self._check_admin(message.from_user.id):
            await message.answer("❌ Эта команда доступна только администраторам")
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("❌ Использование: /admin_delete_room <название>")
            return

        room_name = args[1]

        # Check if room exists
        existing = self.db.get_room(room_name)
        if not existing:
            await message.answer(f"❌ Переговорка '{room_name}' не найдена")
            return

        # Delete all bookings for this room
        deleted_count = self.db.delete_room_bookings(room_name)
        await message.answer(
            f"✅ Переговорка '{room_name}' удалена "
            f"(удалено бронирований: {deleted_count})"
        )

    async def cmd_admin_add(self, message: Message):
        """Admin: add new admin - reply to user's message"""
        if not self._check_admin(message.from_user.id):
            await message.answer("❌ Эта команда доступна только администраторам")
            return

        if not message.reply_to_message:
            await message.answer(
                "❌ Ответьте на сообщение пользователя, которого хотите сделать админом"
            )
            return

        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.full_name

        if self.db.is_admin(user_id):
            await message.answer(f"❌ {username} уже является администратором")
            return

        self.db.add_admin(user_id, username)
        await message.answer(f"✅ {username} добавлен как администратор")

    async def cmd_admin_remove(self, message: Message):
        """Admin: remove admin - reply to user's message"""
        if not self._check_admin(message.from_user.id):
            await message.answer("❌ Эта команда доступна только администраторам")
            return

        if not message.reply_to_message:
            await message.answer(
                "❌ Ответьте на сообщение администратора, которого хотите удалить"
            )
            return

        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.full_name

        if not self.db.is_admin(user_id):
            await message.answer(f"❌ {username} не является администратором")
            return

        self.db.remove_admin(user_id)
        await message.answer(f"✅ {username} удален из администраторов")

    async def cmd_admin_list(self, message: Message):
        """Admin: list all admins"""
        if not self._check_admin(message.from_user.id):
            await message.answer("❌ Эта команда доступна только администраторам")
            return

        admins = self.db.get_all_admins()
        if not admins:
            await message.answer("📋 Нет администраторов")
            return

        lines = ["👥 Администраторы:\n"]
        for admin in admins:
            lines.append(f"• {admin['username']} (ID: {admin['user_id']})")

        await message.answer("\n".join(lines))

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

    async def start(self):
        """Start the bot."""
        await self.dp.start_polling(self.bot)


def main():
    """Entry point for running the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    # Read ADMIN_USER_ID for admin initialization
    admin_user_id = int(os.getenv("ADMIN_USER_ID", 0))

    bot = RoomBookingBot(token)

    # Initialize first admin from .env
    if admin_user_id and not bot.db.is_admin(admin_user_id):
        bot.db.add_admin(admin_user_id, "Initial Admin (from .env)")
        print(f"✅ Initialized admin: {admin_user_id}")
    elif admin_user_id:
        print(f"ℹ️  Admin {admin_user_id} already exists")

    import asyncio
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
