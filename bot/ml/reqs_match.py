import pipreqs.pipreqs
from pydantic import BaseModel, Field

ALLOWED_DEPS = [
    {"name": "falcon", "version": "~=3.0.0"},
    {"name": "gunicorn", "version": "~=20.0.0"},
    {"name": "gevent", "version": "~=21.1.0"},
    {"name": "attrs", "version": "~=21.2.0"},
    {"name": "sqlalchemy", "version": "~=1.4.0"},
    {"name": "alembic", "version": "~=1.7.0"},
    {"name": "kafka-python", "version": "~=2.0.0"},
    {"name": "click", "version": "~=7.1.0"},
    {"name": "numpy", "version": "~=1.21.0"},
    {"name": "pandas", "version": "~=1.3.0"},
    {"name": "openpyxl", "version": "~=3.0.0"},
    {"name": "pydantic", "version": "~=1.8.0"},
    {"name": "pymssql", "version": "~=2.2.0"},
    {"name": "cx-oracle", "version": "~=8.2.0"},
    {"name": "kombu", "version": "~=5.1.0"},
    {"name": "psycopg2", "version": "~=2.9.0"},
    {"name": "PyJWT", "version": "~=2.0.0"},
    {"name": "python-json-logger", "version": "~=2.0.0"},
    {"name": "requests", "version": "~=2.27.0"},
    {"name": "plotly", "version": "~=5.5.0"},
    {"name": "pytest", "version": "~=6.2.0"},
    {"name": "pytest-cov", "version": "~=2.12.0"},
    {"name": "isort", "version": "~=5.10.0"},
    {"name": "yapf", "version": "~=0.32.0"},
    {"name": "toml", "version": "~=0.10.2"},
    {"name": "docxtpl", "version": "~=0.16.4"},
]


NOT_MATCHED_TEMPALTE = "В проекте найдены зависимости, выходящие за рамки стандартных инструментов и библиотек. \
Просьба согласовать следующие зависимости с лидером направления backend разработки:\n{reqs}"


class ReqsMatcherResult(BaseModel):
    type: str = Field(default="reqs_match")
    comment: str


class ReqsMatcher:
    def __init__(
        self,
        message_template: str = NOT_MATCHED_TEMPALTE,
        allowed_deps: list = ALLOWED_DEPS,
    ):
        self.message_template = message_template
        self.allowed_deps = allowed_deps

    def invoke(self, project_path: str) -> ReqsMatcherResult | None:
        imps = pipreqs.pipreqs.get_all_imports(project_path)

        project_lib_names = set(imps)
        allowed_lib_names = {i["name"] for i in self.allowed_deps}

        disallowed_dependencies = project_lib_names - allowed_lib_names

        if disallowed_dependencies:

            reqs = ""
            for dep in sorted(disallowed_dependencies):
                reqs += f"  - {dep}\n"

            result = ReqsMatcherResult(comment=NOT_MATCHED_TEMPALTE.format(reqs=reqs))
            return result

        else:
            return None


if __name__ == "__main__":

    project_path = "/home/artem/work/programming/codereview_hack/example_projects/python/http-api-3.1"

    node = ReqsMatcher()
    result = node.invoke(project_path)
    if result is not None:
        print(result)
    else:
        print("No disallowed libraries found. All dependencies are allowed.")
