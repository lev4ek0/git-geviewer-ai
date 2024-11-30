from tenacity import retry, stop_after_attempt
from pydantic import BaseModel, Field
from typing import List, Dict
from pathlib import Path

from langchain_core.output_parsers import BaseOutputParser, JsonOutputParser, PydanticOutputParser, StrOutputParser
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

from utils import add_line_numbers
from llms import LLMFactory


DATA_PATH = Path(r"D:\ITMO\hacks\llm_review\python\backend-master\freenit\cli.py")


class LoggingCheckerOutput(BaseModel):
    type: str = Field(default="logging")
    start_line_number: int = Field(description="Начало участка кода где есть ошибка (номер строки)")
    end_line_number: int = Field(description="Конец участка кода где есть ошибка (номер строки)")
    comment: str = Field(description="Перечисление всех ошибок в этом участке кода")
    suggestion: str = Field(description="```python\n<Исправленная версия участка кода>\n```")


class ListLoggingCheckerOutput(BaseModel):
    comments: List[LoggingCheckerOutput] = Field(description="Список ошибок найденных в коде")


LOGGING_CHECKER_PROMPT = """
## System
Ты помощник в оценке `.py` скриптов, который занимается проверкой на качество логирования программ, 
используя стандартную библиотеку `logging`. ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ!

## Твоя задача
Тебе на вход приходит текст программы на Python - SCRIPT.
Твоя задача найти ошибки в этом скрипте, которые не соответствуют правилам логирования.
Обязательно находи все ошибки!

## Список требований
- Запрещено использовать print
- Запрещено использовать глобальную настройку logging (Предварительно нужно создать объект логгера). Нужно так:
```python
logger = logging.getLogger(__name__)
logger.info('This is an info log message', extra={{'key': 'value'}})
```
Нельзя так:
```python
logging.info('This is an info log message', extra={{'key': 'value'}})
```
- Запрещено использовать f-строки:
Неверно:
```python
id_ = 1
self.logger.info(f'Transport with id [{{id_}}] was deleted')
```
Верно:
```python
id_ = 1
self.logger.info('Transport with id [%s] was deleted', id_)
```
- Обязательно проверь чтобы в конфиге выставлялись форматы fmt = '%(asctime)s.%(msecs)03d [%(levelname)s]|[%(name)s]: %(message)s' и 
datefmt = '%Y-%m-%d %H:%M:%S'

## Алгоритм проверки
1. Пройдись по каждой строке в SCRIPT.
2. Проверь строку на соответствие требованиям из `Списка требований`.
3. Если строка удовлетворяет требованиям, то переходи к следующей, иначе 
определи участок кода где есть ошибка (сколько строк подряд) и запомни номера строк, саму ошибку и как ее исправить.
4. Если в одной строке находится несколько ошибок, то укажи их все и предложи исправленный вариант как в пункте 3.
5. Повторяй до тех пор пока не закончатся все строки в SCRIPT.

## Формат твоего вывода
Если нашел несоответствия требованиям выше, то верни ответ в следующем формате:
{format_instructions}

ЗАПРЕЩЕНО ДУБЛИРОВАТЬ. Если в коде встречается несколько ошибок, то ты должен вывести их все в нужном формате.
ВАЖНО! Если в коде не встречается никаких print и logging, то просто выводи comments пустым списком.
Не добавляй своих комментарии и рассуждения!!!

## Приступим
SCRIPT:
```python
{script_content}
```
Твой ответ:
"""


class LoggingChecker:
    def __init__(self, llm: BaseChatModel, prompt: str = LOGGING_CHECKER_PROMPT, parser: BaseOutputParser = JsonOutputParser(pydantic_object=ListLoggingCheckerOutput)):
        self._parser_instructions = parser.get_format_instructions()
        self._chain = PromptTemplate.from_template(prompt) | llm | parser
    
    @retry(stop=stop_after_attempt(3))
    def invoke(self, script_content: str):
        with_lines = add_line_numbers(script_content)
        llm_answer = self._chain.invoke({"script_content": with_lines, "format_instructions": ListLoggingCheckerOutput.model_json_schema()})
        return ListLoggingCheckerOutput.model_validate(llm_answer)


if __name__ == "__main__":
    llm = LLMFactory.get_llm("mistral-nemo-instruct-2407")

    checker = LoggingChecker(llm)
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        contents = f.read()

    result = checker.invoke(contents)
    print(result)
