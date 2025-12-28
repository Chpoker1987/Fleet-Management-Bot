from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from src.database.models import VehicleRepository

web_router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@web_router.get("/dashboard")
async def get_dashboard(request: Request):
    # Получение данных из БД асинхронно
    vehicles = await VehicleRepository.get_all_vehicles()

    # Считывание простой статистики
    total = len(vehicles)
    active = sum(1 for v in vehicles if v.status == "OnRoute")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "vehicles": vehicles,
        "stats": {"total": total, "active": active}
    })
