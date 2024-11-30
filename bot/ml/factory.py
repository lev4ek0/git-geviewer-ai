from pathlib import Path

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


async def get_ml_response(path: str, language: str) -> OutputJson:
    print(language)
    list_files_in_directory(path)
    code_comments = [
        create_code_comment(x, i) for x in range(1, 5) for i in range(1, 4)
    ]

    project_comments = [create_project_comment(x) for x in range(1, 5)]

    return OutputJson(
        titles=["Раздел 1", "Раздел 2", "Раздел 3", "Раздел 4"],
        code_comments=code_comments,
        project_comments=project_comments,
    )
