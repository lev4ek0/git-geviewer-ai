import asyncio
import logging

from admin import MyAdmin
from admin.admin import admin_router
from admin.auth import admin_auth_backend
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from api import review_router
from database import engine, postgres_connection, redis_connection
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from handlers import router as all_routers
from prometheus_client import start_http_server
from settings import bot_settings, redis_settings


async def on_startup():
    await postgres_connection.connect()
    redis_connection.connect()


app = FastAPI(
    title="Admin",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
admin = MyAdmin(
    app, engine, base_url="/admin-auth", authentication_backend=admin_auth_backend
)
admin.include_router(admin_router)
app.include_router(review_router, prefix="/api")


async def main():
    TOKEN = bot_settings.TOKEN.get_secret_value()

    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    storage = RedisStorage.from_url(
        f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}/0"
    )
    dp = Dispatcher(storage=storage)
    dp.include_router(all_routers)
    if is_polling := bot_settings.IS_POLLING:
        await on_startup()
        await dp.start_polling(bot)


if __name__ == "__main__":
    start_http_server(9091)
    asyncio.run(main())
