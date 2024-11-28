from admin import AdminRouter
from database.models import Chat
from sqladmin import ModelView

router = AdminRouter()


@router.view
class ChatAdmin(ModelView, model=Chat):
    icon = "fa-solid fa-c"
    form_excluded_columns = [Chat.created_at, Chat.updated_at]
    column_list = [Chat.id, "message_count"]
    column_searchable_list = [Chat.id]
