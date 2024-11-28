from aiogram import Router
from handlers.start import router as start_router
from middleware import (
    ErrorsMiddleware,
    MetricsMiddleware,
    SessionMiddleware,
    UserMiddleware,
)

user_middleware = UserMiddleware()
session_middleware = SessionMiddleware()

router = Router()
router.include_routers(start_router)


router.message.middleware(session_middleware)
router.callback_query.middleware(session_middleware)
router.message.middleware(user_middleware)
router.callback_query.middleware(user_middleware)
router.message.middleware(ErrorsMiddleware())
router.message.middleware(MetricsMiddleware())


__all__ = (
    "router",
    "create_router",
)
