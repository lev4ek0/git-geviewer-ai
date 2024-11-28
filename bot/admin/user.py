from admin import AdminRouter
from database import User
from sqladmin import ModelView

router = AdminRouter()


@router.view
class UserAdmin(ModelView, model=User):
    icon = "fa-solid fa-user"
    column_list = [User.telegram_id, User.full_name, User.is_banned]
    column_searchable_list = [User.telegram_id, User.full_name]
    column_default_sort = "created_at"
    form_excluded_columns = [User.created_at, User.updated_at]
