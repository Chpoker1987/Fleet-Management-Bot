from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.models import VehicleRepository
from src.bot.states import VehicleForm

router = Router()
dashboard_url = "https://nontaxonomical-coleman-homological.ngrok-free.dev/dashboard"


# --- Стандартные команды ---
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚛 Открыть Дашборд", web_app=WebAppInfo(url=dashboard_url))]
    ])

    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        "Я бот управления автопарком. Используй меню для навигации или введи /help.",
        reply_markup=markup
    )


@router.message(Command("about"))
async def cmd_about(message: types.Message):
    """Информация о проекте"""
    text = (
        "📚 **О проекте: Fleet Management System**\n\n"
        "Система предназначена для оперативного управления логистикой.\n"
        "• **Стек:** Python 3.14, Aiogram 3, FastAPI, SQLAlchemy.\n"
        "• **Архитектура:** Hybrid Monolith (Bot + Web).\n"
        "• **Версия:** 0.0.1 (Alpha)."
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Список команд"""
    text = (
        "🛠 **Доступные команды:**\n\n"
        "/start - Запуск и ссылка на дашборд\n"
        "/add - ➕ Добавить новую машину\n"
        "/about - О проекте\n"
        "/cancel - Отмена текущего действия"
    )
    await message.answer(text)


# --- FSM: Добавление машины ---
@router.message(Command("add"))
async def start_add_vehicle(message: types.Message, state: FSMContext):
    """Начало диалога добавления"""
    await message.answer("✍️ Введите государственный номер автомобиля (например, A777AA):")
    # Переводим бота в состояние ожидания номера
    await state.set_state(VehicleForm.waiting_for_plate)


@router.message(StateFilter(VehicleForm.waiting_for_plate))
async def process_plate(message: types.Message, state: FSMContext):
    """Получаем номер и спрашиваем водителя"""
    plate = message.text.upper().strip()

    # Валидация (простая)
    if len(plate) < 6:
        await message.answer("⚠️ Слишком короткий номер. Попробуйте еще раз:")
        return

    # Сохраняем номер во временную память (в контекст состояния)
    await state.update_data(plate=plate)

    await message.answer(f"Принято: {plate}.\n👤 Теперь введите ФИО водителя:")
    # Переходим к следующему шагу
    await state.set_state(VehicleForm.waiting_for_driver)


@router.message(StateFilter(VehicleForm.waiting_for_driver))
async def process_driver(message: types.Message, state: FSMContext):
    """Получаем водителя и сохраняем в БД"""
    driver_name = message.text.strip()

    # Получение данных
    data = await state.get_data()
    plate = data['plate']

    try:
        # ⚡️ Записывает в базу данных
        await VehicleRepository.add_vehicle(plate, driver_name)

        await message.answer(
            f"✅ **Успешно добавлено!**\n\n"
            f"🚛 Авто: `{plate}`\n"
            f"👤 Водитель: {driver_name}\n\n"
            f"Данные уже обновились на Дашборде.",
            parse_mode="Markdown"
        )
    except Exception as e:
        # Ловим ошибку (например, если такой номер уже есть)
        await message.answer(f"❌ Ошибка при сохранении: {e}")

    # Сбрасываем состояние (диалог завершен)
    await state.clear()


# --- Отмена действия ---
@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return

    await state.clear()
    await message.answer("⛔️ Действие отменено.")
