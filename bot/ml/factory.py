from pathlib import Path

from ml.code_analyzer import CodeAnalyzer
from ml.code_reviewer import CodeReviewer
from ml.files_parser import FilesParser
from ml.layer_classifier import LayerClassifier
from ml.logging_checker import LoggingChecker
from ml.project_structure_analyzer import ProjectStructureAnalyzer
from ml.reqs_match import ReqsMatcher
from schemas.ml import CodeComment, OutputJson, ProjectComment


def create_code_comment(title_number: int, comment_number: int):
    return CodeComment(
        title=f"Раздел {title_number}",
        start_string_number=10,
        end_string_number=15,
        filepath=f"/project/file{comment_number}.py",
        comment=f"Комментарий {comment_number}",
        suggestion=f"Рекомендация {comment_number}",
    )


def create_project_comment(title_number: int):
    return ProjectComment(
        title=f"Раздел {title_number}",
        comment=f"Комментарий 1",
    )


def list_files_in_directory(path):
    # Создаем объект Path
    dir_path = Path(path)

    # Проверяем, что путь существует и это директория
    if dir_path.exists() and dir_path.is_dir():
        # Перебираем все файлы в директории
        for file in dir_path.iterdir():
            print(file.name)
    else:
        print(f"Путь {path} не существует или это не директория")


json = {
    "titles": ["Архитектурные ошибки", "Логирование", "Недопустимые зависимости"],
    "code_comments": [
        {
            "title": "Архитектурные ошибки",
            "start_string_number": 20,
            "end_string_number": 80,
            "filepath": "versions/06a043f2516a_initial.py",
            "comment": "Этот код создает таблицы в базе данных, что является задачей слоя adapters. Однако, код также определяет структуру таблиц, что является задачей слоя core. Рекомендуется перенести определение структуры таблиц в слой core, а в слой adapters оставить только код создания/удаления таблиц.",
            "suggestion": None,
        },
        {
            "title": "Архитектурные ошибки",
            "start_string_number": 4,
            "end_string_number": 6,
            "filepath": "env.py",
            "comment": "Эти импорты не относятся к слою composite, их нужно перенести в слой core или adapters в зависимости от того, к чему они относятся.",
            "suggestion": None,
        },
        {
            "title": "Архитектурные ошибки",
            "start_string_number": 8,
            "end_string_number": 9,
            "filepath": "env.py",
            "comment": "Эти строки не относятся к слою composite, их нужно перенести в слой core.",
            "suggestion": None,
        },
        {
            "title": "Архитектурные ошибки",
            "start_string_number": 11,
            "end_string_number": 15,
            "filepath": "env.py",
            "comment": "Этот участок кода относится к слою composite, но он может быть вынесен в отдельный сервис в слое core, чтобы следовать принципу единственной ответственности.",
            "suggestion": None,
        },
        {
            "title": "Логирование",
            "start_string_number": 12,
            "end_string_number": 12,
            "filepath": "env.py",
            "comment": "Использование print",
            "suggestion": "```python\nlogger = logging.getLogger(__name__)\nlogger.info('This is an info log message', extra={'key': 'value'})\n```",
        },
    ],
    "project_comments": [
        {
            "title": "Недопустимые зависимости",
            "comment": "В проекте найдены зависимости, выходящие за рамки стандартных инструментов и библиотек. Просьба согласовать следующие зависимости с лидером направления backend разработки:\n  - freenit\n",
        }
    ],
}


async def get_ml_response(path: str, language: str) -> OutputJson | None:
    if language != "py":
        return None

    from ml.llms import LLMFactory

    llm = LLMFactory.get_llm("mistral-nemo-instruct-2407")

    reviewer = CodeReviewer(
        FilesParser(),
        LayerClassifier(llm),
        ProjectStructureAnalyzer(llm),
        ReqsMatcher(),
        scripts_validators=[CodeAnalyzer(llm), LoggingChecker(llm)],
    )
    EXTENSION = ".py"
    result = reviewer.invoke(path, EXTENSION)

    return result
