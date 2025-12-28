import asyncio
import os
import uvicorn
import sys
from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from dotenv import load_dotenv

from src.bot.handlers import router as bot_router
from src.web.routes import web_router
from src.database.models import VehicleRepository
from pyngrok import ngrok
from src.bot.handlers import dashboard_url

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Setup FastAPI
app = FastAPI()
app.include_router(web_router)

# Setup Bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(bot_router)


async def start_bot():
    """Запуск полинга бота"""
    # Удаление вебхук для чистого старта поллинга
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def monitor_console(server: uvicorn.Server):
    """ Слушает консоль в отдельном потоке.
    Если ввести 'exit', инициирует остановку сервера.
    """
    while True:
        # await asyncio.to_thread запускает блокирующую функцию input()
        # в отдельном потоке, не останавливая бота
        cmd = await asyncio.to_thread(input)
        if cmd.strip().lower() == "exit":
            print("🛑 Stopping system initiated by admin...")
            server.should_exit = True
            # Остановка поллинга бота
            await dp.stop_polling()
            # Закрытие сессии бота
            await bot.session.close()
            break


async def main():
    # Запуск туннеля через ngrok
    if ngrok:
        # Закрывает старые туннели, если они "зависли"
        ngrok.kill()
        # Открывает новый
        try:
            #public_url = ngrok.connect(8000).public_url
            print(f"\n🚀 --- SYSTEM ONLINE ---")
            print(f"🌍 Public Ngrok URL: {dashboard_url}", end=None)
            #print(f"(Ссылка создана, файл handlers.py нужно изменить)\n")
            #print(f"(Ccылка - {public_url}")
        except Exception as e:
            print(f"⚠️ Ngrok warning: {e}")
    # Инициализация БД
    await VehicleRepository.init_db()

    # Создание тестовых данных (если база пустая)
    vehicles = await VehicleRepository.get_all_vehicles()
    if not vehicles:
        await VehicleRepository.add_vehicle("A001AA", "Иванов И.И.")
        await VehicleRepository.add_vehicle("B002BB", "Петров П.П.")

    # Запуск сервера и бота параллельно
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    # Запускаем Uvicorn и Bot Polling конкурентно
    await asyncio.gather(
        server.serve(),
        start_bot(),
        monitor_console(server)
    )
    print("✅ System shutdown complete. Port 8000 released.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
