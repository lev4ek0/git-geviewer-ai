from database.models import User
from fastapi import Request
from settings.settings import bot_settings
from sqladmin.authentication import AuthenticationBackend
from utils import handle_auth_errors


class AdminAuth(AuthenticationBackend):
    @staticmethod
    def is_admin_role(user: User | None) -> bool:
        return user and user.is_superuser

    @handle_auth_errors
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        request.session.update(
            {"token": hash(bot_settings.ADMIN_PASSWORD.get_secret_value())}
        )
        return (
            username == bot_settings.ADMIN_USERNAME
            and password == bot_settings.ADMIN_PASSWORD.get_secret_value()
        )

    @handle_auth_errors
    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    @handle_auth_errors
    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        return token == hash(bot_settings.ADMIN_PASSWORD.get_secret_value())


admin_auth_backend = AdminAuth(bot_settings.SECRET_KEY.get_secret_value())
