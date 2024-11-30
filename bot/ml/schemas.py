from pydantic import BaseModel, Field


class CodeComment(BaseModel):
    title: str = Field(description="Название раздела")
    start_string_number: int = Field(description="Номер строки (начало)")
    end_string_number: int = Field(description="Номер строки (конец)")
    filepath: str = Field(description="Путь до файла")
    comment: str = Field(description="Комментарий к участку кода")
    suggestion: str = Field(description="Рекомендации по исправлению", default=None)


class ProjectComment(BaseModel):
    title: str = Field(description="Название раздела")
    comment: str = Field(description="Комментарий")


class OutputJson(BaseModel):
    titles: list[str] = Field(description="Список возможных разделов, к которым относятся комментарии")
    code_comments: list[CodeComment]
    project_comments: list[ProjectComment]
