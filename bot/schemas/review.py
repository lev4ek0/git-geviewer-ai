from uuid import UUID

from pydantic import Field
from schemas.base import BaseModel


class UploadFileReponseSchema(BaseModel):
    report_id: UUID


class LineSchema(BaseModel):
    order: int = Field(description="Номер строки")
    text: str = Field(description="Строка кода")


class CodeCommentSchema(BaseModel):
    title: str = Field(description="Название раздела")
    lines: list[LineSchema]
    start_string_number: int = Field(description="Номер строки (начало)")
    end_string_number: int = Field(description="Номер строки (конец)")
    filepath: str = Field(description="Путь до файла")
    comment: str = Field(description="Комментарий к участку кода")
    suggestion: str = Field(description="Рекомендации по исправлению", default=None)


class ProjectCommentSchema(BaseModel):
    title: str = Field(description="Название раздела")
    comment: str = Field(description="Комментарий")


class ReviewSchema(BaseModel):
    id: UUID
    titles: list[str] = Field(
        description="Список возможных разделов, к которым относятся комментарии"
    )
    code_comments: list[CodeCommentSchema]
    project_comments: list[ProjectCommentSchema]
