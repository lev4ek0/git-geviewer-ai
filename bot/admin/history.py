from admin import AdminRouter
from database.models import History
from sqladmin import ModelView

router = AdminRouter()


@router.view
class HistoryAdmin(ModelView, model=History):
    icon = "fa-solid fa-h"
    column_list = [History.command, "name"]
    column_searchable_list = [History.user_id, History.command, "user.full_name"]
    form_excluded_columns = [History.created_at, History.updated_at]
