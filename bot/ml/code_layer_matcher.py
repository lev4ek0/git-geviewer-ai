import os

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.exceptions import OutputParserException

import utils
from llms import LLMFactory


class CodeLayerMatchComment(BaseModel):
    start_string_number: int = Field(description="Номер строки (начало участка кода)")
    end_string_number: int = Field(description="Номер строки (конец участка кода)")
    comment: str = Field(
        description="Комментарий к участку кода и то, куда его надо перенести"
    )


class CodeLayerMatchResult(BaseModel):
    comments: list[CodeLayerMatchComment] = Field(description="Комментарии к коду")


# TODO изменить описание слоев

CODE_LAYER_MATCH_PROMPT = """
Ты - полезный AI рецензент кода. Ты отвечаешь только на русском языке.

## Твоя задача
Тебе на вход приходит содержимое файла FILE, а также структура проекта. Ты должен проверить код в этом файле на соответствие слою приложения, к которому относится данный файл.

## Описание слоев приложения
1. **core**
В слое приложения лежит все что относится к бизнес логике (сущности, DTO, константы, DS модель,
сервисы и тд. и тп). Этот слой не зависит от интеграций (адаптеров). Для этого применяется
механизм DI. В слое приложения описываются интерфейсы получения данных, в адаптерах они
реализуются.
2. **adapters**
В адаптерах лежат интеграции со внешними сервисами. Там же лежат и буквы VC из MVC веб
библиотеки, CLI, продьюсеры, консьюмеры и прочие интеграционные компоненты (например api
клиенты). Первичные и вторичные адаптеры могут быть в одном каталоге.
3. **composite**
Тут происходит сборка компонентов для запуска процесса. Именно тут инициализируются настройки,
внедряются зависимости.

{project_tree}

Путь до файла: {file_path}

Данный файл относится к слою {layer_name}. Твоя задача - проверить, соответствует ли код этому слою. Если какие-то части кода не соответсвуют этому слою, напиши, куда их нужно перенести. Не пиши положительные комментарии к коду.

## FILE
```python
{file_content}
```

Ответ верни ОБЯЗАТЕЛЬНО в формате JSON со следующей структурой:
```json
{format_instructions}
```
"""


class CodeLayerMatcher:
    def __init__(self, llm, prompt: str = CODE_LAYER_MATCH_PROMPT):
        output_parser = PydanticOutputParser(pydantic_object=CodeLayerMatchResult)
        self._chain = PromptTemplate.from_template(prompt) | llm | output_parser

    def invoke(
        self, project_path: str, layer_name: str, file_relative_path: str
    ) -> CodeLayerMatchResult:
        with open(os.path.join(project_path, file_path), "r") as f:
            file_content = f.read()
        file_content = utils.add_line_numbers(file_content)

        tree_generator = utils.DirectoryTreeGenerator(project_path)
        tree_str = tree_generator.get_tree()
        
        try:
            ai_msg = self._chain.invoke(
                {
                    "format_instructions": CodeLayerMatchResult.model_json_schema(),
                    # "project_tree": tree_str,
                    "project_tree": "",
                    "file_path": file_relative_path,
                    "layer_name": layer_name,
                    "file_content": file_content,
                }
            )
        except OutputParserException:
            ai_msg = CodeLayerMatchResult(comments=[])
        
        return ai_msg


if __name__ == "__main__":

    llm = LLMFactory.get_llm("Qwen/Qwen2.5-Coder-32B-Instruct")

    # project_path = "/home/artem/work/programming/codereview_hack/example_projects/python/gramps-web-api-master/"
    # layer_name = "core"
    # file_path = "gramps_webapi/api/emails.py"

    project_path = "/home/artem/work/programming/codereview_hack/example_projects/python/donna-backend-master/donna-backend-master"
    layer_name = "adapters"
    file_path = "app/services/user_services.py"

    node = CodeLayerMatcher(llm)
    result = node.invoke(project_path, layer_name, file_path)

    print(result)
