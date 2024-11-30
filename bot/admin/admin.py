from admin import AdminRouter
from admin.chat import router as chat_router
from admin.history import router as history_router
from admin.report import router as report_router
from admin.user import router as user_router

admin_router = AdminRouter()
admin_router.include_routers(
    [
        user_router,
        chat_router,
        history_router,
        report_router,
    ]
)
