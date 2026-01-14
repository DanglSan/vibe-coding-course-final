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

# Load environment variables
load_dotenv()


class RoomBookingBot:
    """Telegram bot for managing room bookings."""

    def __init__(self, token: str, db_path: str = "bookings.db"):
        """Initialize bot."""
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.db = Database(db_path)

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

    async def cmd_start(self, message: Message):
        """Handle /start command."""
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

    async def start(self):
        """Start the bot."""
        await self.dp.start_polling(self.bot)


def main():
    """Entry point for running the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    # Read ADMIN_USER_ID for future admin features
    admin_user_id = int(os.getenv("ADMIN_USER_ID", 0))
    if admin_user_id:
        print(f"Admin user ID configured: {admin_user_id}")

    bot = RoomBookingBot(token)
    import asyncio
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
