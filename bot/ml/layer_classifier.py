from typing import List, Dict
from pathlib import Path
import json
import re

from langchain_core.output_parsers import StrOutputParser, BaseOutputParser
from langchain_core.prompts import PromptTemplate

from files_parser import FilesParser


DATA_PATH = r"D:\ITMO\hacks\llm_review\python\backend-master"


LAYER_CLASSIFIER_PROMPT = """
## System prompt
Ты помощник в ревью кода. Ты отвечаешь только на русском языке.

## Твоя задача
Тебе на вход приходит структура проекта PROJECT в виде словаря Python, где ключи - путь до директории, а значения - список скриптов `.py`.
Этот проект должен соответствовать "Гексагональной" архитектуре.
Твоя задача классифицировать каждую директорию (ключи словаря) на один из НЕСКОЛЬКИХ классов.
Для этого используй представление о том как должен выглядеть гексагональный проект, имена директорий и файлов. Примерно представь что может в них находится для успешной
классификации.

## Описание классов
1. **core**
В слое приложения лежит все что относится к бизнес логике (сущности, DTO, константы, DS модель,
сервисы и тд. и тп). Этот слой не зависит от интеграций (адаптеров). Для этого применяется
механизм DI. В слое приложения описываются интерфейсы получения данных, в адаптерах они
реализуются.
2. **adapters**
В адаптерах лежат интеграции со внешними сервисами. Там же лежат и буквы VC из MVC веб
библиотеки, CLI, продьюсеры, консьюмеры и прочие интеграционные компоненты (например api
клиенты). Первичные и вторичные адаптеры могут быть в одном каталоге. Работа с базой данных (описание таблиц, миграции, код запросов) лежат во вторичных адаптерах.
Нужно понимать, что в компании есть разные СУБД (преимущественно MSSQL и Postgres),
3. **composite**
Тут происходит сборка компонентов для запуска процесса. Именно тут инициализируются настройки,
внедряются зависимости. Чаще всего здесь находятся файлы `settings.py`
4. **tests**
Модули для тестирования приложения. unit тесты и интеграционные тесты.
5. **docs**
Документация.

## Формат вывода
ОБЯЗАТЕЛЬНО выдай ответ в виде JSON где ключи - путь до директории (НЕ ФАЙЛА!), а значения - результат классификации
с указанием класса.
Не добавляй свои рассуждения!

Формат вывода:
```json
<Твой ответ>
```

PROJECT:
{project}
Твой ответ:
"""


class LayerClassifier:
    def __init__(self, llm, prompt: str = LAYER_CLASSIFIER_PROMPT, output_parser: BaseOutputParser = StrOutputParser()):
        self._chain = PromptTemplate.from_template(prompt) | llm | output_parser

    def invoke(self, project_structure: Dict[str, List[str]]) -> Dict:
        template = {str(k): v for k, v in project_structure.items()}
        answer = self._chain.invoke({"project": template})
        answer_json = json.loads(re.findall(r"```json\n(.*)\n```", answer, re.DOTALL)[0])
        return {Path(k): v for k, v in answer_json.items()}


if __name__ == "__main__":
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="Qwen/Qwen2.5-Coder-32B-Instruct",
        api_key="U3NKiHbEzT2Fcqyb0X5OWQyTFDIcFQbV",
        base_url="https://api.deepinfra.com/v1/openai",
    )

    classifier = LayerClassifier(llm, LAYER_CLASSIFIER_PROMPT, StrOutputParser())
    project_structure = FilesParser().invoke(DATA_PATH)

    print(classifier.invoke(project_structure))
