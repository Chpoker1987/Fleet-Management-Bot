import os
from sqlalchemy import String, Integer, Float, select
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# --- Config ---
DATABASE_URL = "sqlite+aiosqlite:///./fleet.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# --- Base Model ---
class Base(AsyncAttrs, DeclarativeBase):
    pass


# --- Domain Model ---
class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    driver_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="Idle")  # Idle, OnRoute, Maintenance
    mileage: Mapped[float] = mapped_column(Float, default=0.0)


# --- Repository (Data Access Layer) ---
class VehicleRepository:
    """Логика базы данных."""

    @staticmethod
    async def get_all_vehicles():
        async with async_session() as session:
            result = await session.execute(select(Vehicle))
            return result.scalars().all()

    @staticmethod
    async def add_vehicle(plate: str, driver: str):
        async with async_session() as session:
            # Проверяем, нет ли уже такой машины
            existing = await session.execute(select(Vehicle).where(Vehicle.plate_number == plate))
            if existing.scalar():
                raise ValueError(f"Машина с номером {plate} уже существует!")
            new_vehicle = Vehicle(plate_number=plate, driver_name=driver)
            session.add(new_vehicle)
            await session.commit()
            return new_vehicle

    @staticmethod
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
