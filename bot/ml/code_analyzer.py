import os
from typing import Literal

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from ml import utils
from ml.llms import LLMFactory
from pydantic import BaseModel, Field

error_type = Literal["architecture", "auth", "data"]


class CodeAnalyzerComment(BaseModel):
    type: error_type = Field(description="Тип найденной ошибки")
    start_line_number: int = Field(
        description="Номер строки (начало участка кода с ошибкой)"
    )
    end_line_number: int = Field(
        description="Номер строки (конец участка кода с ошибкой)"
    )
    comment: str = Field(
        description="Комментарий к ошибке, найденной на этом участке кода"
    )


class CodeAnalyzerCommentResult(BaseModel):
    comments: list[CodeAnalyzerComment] = Field(description="Комментарии к коду")


CODE_ANALYZER_PROMPT = """
Ты - полезный AI рецензент кода. Ты отвечаешь только на русском языке.

## Твоя задача
Тебе на вход приходит содержимое файла FILE в python проекте. Ты должен проверить код в этом файле на наличие ошибок нескольких типов.

## Типы ошибок
### Первый тип ошибки - **architecture**
Архитектурные ошибки. Необходимо проверить, соответствует ли код в этом файле слою приложения.
В проекте должна использоваться "Гексагональная" архитектура, цель которой - отделить основную бизнес-логику приложения от сервисов, которые оно использует.
"Гексагональная" архитектура подразумевает наличие 3-х слоев приложения: core, adapters, composites.
#### Описание слоев приложения
1. **core**
**Ключевые признаки**:
- Содержит доменные сущности, бизнес-правила, DTO, ошибки и сервисы.
- Не зависит от внешних интеграций и инфраструктуры.
- Работает только с интерфейсами для взаимодействия с адаптерами (репозитории, шлюзы, API-клиенты).
- Сущности описывают поведение и инварианты, а не только данные.
- Для передачи данных между слоями используются DTO, а не примитивные структуры (словари, списки и т. д.).
- Код, связанный с анализом данных (feature engineering и моделями), выделяется в отдельные пакеты в core.
- Выполняется валидация данных через pydantic-модели при вызове методов сервисов.
**Основные роли**:
- Управление и реализация бизнес-логики.
- Хранение доменных знаний и правил.
- Описание ошибок и валидации данных.
- Предоставление интерфейсов для работы с данными (реализуются в адаптерах).
**Примеры компонентов**:
- Сервисы (например, UserService для управления пользователями).
- Доменные сущности (например, User, содержащий поведение и бизнес-правила).
- DTO (например, UserDTO для передачи данных).
- Интерфейсы репозиториев (UserRepository).

2. **adapters**
**Ключевые признаки**:
- Это слой интеграций со всем внешним миром.
- Реализует интерфейсы, описанные в core (репозитории, шлюзы, API-клиенты).
- Содержит код для работы с базами данных, внешними API, очередями, веб-серверами и т. д.
- Может содержать адаптеры для взаимодействия с пользовательскими интерфейсами (например, веб-контроллеры, CLI).
- Бизнес-логика не реализуется в адаптерах — только инфраструктурные задачи.
- В сложных проектах возвращаются ORM-объекты; в простых — DTO.
**Основные роли**:
- Реализация интерфейсов, описанных в core.
- Интеграция с внешними системами (базы данных, API, очереди).
- Предоставление данных для использования в core.
**Примеры компонентов**:
- Реализации репозиториев (SQLUserRepository, работающий с базой данных).
- Веб-контроллеры (UserController).
- Консьюмеры и продьюсеры очередей.
- API-клиенты для внешних систем.
- Таблицы баз данных, описанные через ORM.

3. **composites**
**Ключевые признаки**:
- Отвечает за сборку, настройку и запуск приложения.
- Выполняет внедрение зависимостей (DI) для всех слоев.
- Собирает инфраструктурные компоненты, сервисы и адаптеры в единую систему.
- Настраивает параметры и конфигурации приложения.
- Передает зависимости (например, репозитории, сервисы) в адаптеры (например, HTTP API).
**Основные роли**:
- Инициализация приложения.
- Настройка и внедрение всех зависимостей.
- Управление жизненным циклом приложения.
**Примеры компонентов**:
- Инициализация подключения к базе данных (например, sqlalchemy engine).
- Регистрация компонентов веб-приложения (например, контроллеров).
- Сборка и передача зависимостей в адаптеры.
- Запуск HTTP-сервера (например, через gunicorn).

Данный файл FILE относится к слою {layer_name}. Твоя задача - проверить, соответствует ли код этому слою. Если какие-то части кода не соответсвуют этому слою, напиши, куда их нужно перенести.


### Второй тип ошибки - **auth**
Ошибки, связанные с аутентификация и авторизация. Нужно проверить правильность обработки JWT токенов и защиты доступа к ресурсам.
Фронтенд приложения ходит в keycloak и получает токен, этот токен является JWT токеном и расшифровывается стандартными средствами, мы используем пакет pyjwt. В токене находится вся информация о пользователе. Токен передается как bearer в стандартном заголовке Authorization (пример: Authorization: Bearer ...)


### Третий тип ошибки - **data**
Ошибки, связанные с использованием диалект-зависимых конструкций. В компании есть разные СУБД (преимущественно MSSQL и Postgres), поэтому нужно использовать как можно меньше диалекто-зависимых конструкций, а если все-таки использвать, то помечать как `# TODO: dialect dependent`. Также в эту категорию ошибок входит производительность кода, особенно при работе с большими объемами данных.


## Входные данные

Дерево директории проекта:
{project_tree}

Путь до файла FILE: {file_path}

Данный файл FILE относится к слою {layer_name}

### Содержимое FILE
```python
{file_content}
```

## Результат
Не пиши положительные комментарии к коду!
Ответ верни ОБЯЗАТЕЛЬНО в формате JSON со следующей структурой:
```json
{format_instructions}
```
"""


class CodeAnalyzer:
    def __init__(self, llm, prompt: str = CODE_ANALYZER_PROMPT):
        output_parser = PydanticOutputParser(pydantic_object=CodeAnalyzerCommentResult)
        self._chain = PromptTemplate.from_template(prompt) | llm | output_parser

    def invoke(
        self, script_content: str, layer_name: str, file_relative_path: str
    ) -> CodeAnalyzerCommentResult:
        file_content = utils.add_line_numbers(script_content)

        # tree_generator = utils.DirectoryTreeGenerator(project_path)
        # tree_str = tree_generator.get_tree()

        try:
            ai_msg = self._chain.invoke(
                {
                    "format_instructions": CodeAnalyzerCommentResult.model_json_schema(),
                    # "project_tree": tree_str,
                    "project_tree": "",
                    "file_path": file_relative_path,
                    "layer_name": layer_name,
                    "file_content": file_content,
                }
            )
        except OutputParserException:
            ai_msg = CodeAnalyzerCommentResult(comments=[])

        return ai_msg


if __name__ == "__main__":
    llm = LLMFactory.get_llm("Qwen/Qwen2.5-Coder-32B-Instruct")

    # project_path = "/home/artem/work/programming/codereview_hack/example_projects/python/gramps-web-api-master/"
    # layer_name = "core"
    # file_path = "gramps_webapi/api/emails.py"

    project_path = "/home/artem/work/programming/codereview_hack/example_projects/python/donna-backend-master/donna-backend-master"
    # project_path = r"D:\ITMO\hacks\llm_review\python\donna-backend-master"
    layer_name = "adapters"
    file_path = "app/services/user_services.py"

    with open(os.path.join(project_path, file_path), "r") as f:
        file_content = f.read()

    node = CodeAnalyzer(llm)
    result = node.invoke(file_content, layer_name, file_path)

    print(result)
