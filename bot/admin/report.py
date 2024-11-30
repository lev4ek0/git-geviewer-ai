from admin import AdminRouter
from database import Report
from sqladmin import ModelView

router = AdminRouter()


@router.view
class ReportAdmin(ModelView, model=Report):
    icon = "fa-solid fa-h"
    column_list = [Report.pdf_file_path, Report.id]
    column_searchable_list = [Report.pdf_file_path, Report.id]
    form_excluded_columns = [Report.created_at, Report.updated_at]
