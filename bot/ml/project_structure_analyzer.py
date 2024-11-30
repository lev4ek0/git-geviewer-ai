import os

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from ml import utils
from ml.llms import LLMFactory
from pydantic import BaseModel, Field


class ProjectStructureComment(BaseModel):
    type: str = Field(default="project_structure")
    comment: str = Field(description="Недочет, найденный в структуре проекта")


class ProjectStructureResult(BaseModel):
    comments: list[ProjectStructureComment] = Field(
        description="Список недочетов, найденных в структуре проекта"
    )


PROJECT_STRUCTURE_ANALYZER_PROMPT = """
Ты - полезный AI рецензент кода. Ты отвечаешь только на русском языке.

## Твоя задача
Тебе на вход приходит ASCII репрезентация TREE структуры дерева проекта. Ты должен проверить ее на соответствие требованиям, которые будут описаны ниже.

### Требования:
- в корне лежит .gitignore
- в корне лежит .editorconfig
- в корне лежит .gitattributes
- в deployment лежат файлы для CI/CD
- в docs храним тех. документацию (схемы строим с помощью PlantUml)
  * схема прецедентов
  * схема базы данных
  * схема развертывания
  * схема компонентов
- в корне лежит каталог "components", который нужен, чтобы разделить фронтенд и бэкенд.
- в проекте должна использоваться "Гексагональная" архитектура бэкенда, цель которой - отделить основную бизнес-логику приложения от сервисов, которые оно использует. "Гексагональная" архитектура подразумевает наличие 3-х слоев приложения: application, adapters, composites, разбитых на 3 отдельные директории с названиями application, adapters и composites соответственно, внутри каталог с файлами бэкенда.
- каталог бэкенда оформляется в виде стандартного python пакета
- в setup.py описываются метаданные пакета и зависимости, допускается использование setup.cfg
- в pyproject.toml описываются различные конфиги сборщиков, автоформаттеров и тд. и тп.
- README.md c кратким описанием проекта, указаниями как развернуть на локальной машине/контейнере, как запустить тесты, схема прав/групп и т.д.

## Входные данные

TREE структура дерева проекта:
```
{project_tree}
```

## Результат
Составь список найденных недочетов в структуре проекта TREE относительно заданных требований. Не пиши положительные комментарии!
Ответ верни ОБЯЗАТЕЛЬНО в формате JSON со следующей структурой:
```json
{format_instructions}
```
"""


class ProjectStructureAnalyzer:
    def __init__(self, llm, prompt: str = PROJECT_STRUCTURE_ANALYZER_PROMPT):
        output_parser = PydanticOutputParser(pydantic_object=ProjectStructureResult)
        self._chain = PromptTemplate.from_template(prompt) | llm | output_parser

    def invoke(self, project_path: str) -> ProjectStructureResult:
        tree_generator = utils.DirectoryTreeGenerator(project_path)
        tree_str = tree_generator.get_tree()

        try:
            ai_msg = self._chain.invoke(
                {
                    "format_instructions": ProjectStructureResult.model_json_schema(),
                    "project_tree": tree_str,
                }
            )
        except OutputParserException:
            ai_msg = ProjectStructureResult(comments=[])

        return ai_msg


if __name__ == "__main__":
    llm = LLMFactory.get_llm("Qwen/Qwen2.5-Coder-32B-Instruct")
    project_path = "/home/artem/work/programming/codereview_hack/example_projects/python/gramps-web-api-master/"

    node = ProjectStructureAnalyzer(llm)
    result = node.invoke(project_path)

    print(result)
