from pathlib import Path

from layer_classifier import LayerClassifier 
from files_parser import FilesParser


DATA_PATH = r"D:\ITMO\hacks\llm_review\python\backend-master"

class CodeReviewer:
    def __init__(
        self,
        files_parser: FilesParser,
        layer_classifier: LayerClassifier,
    ):
        self.files_parser = files_parser
        self.layer_classifier = layer_classifier

    def invoke(self, source_dir: Path):
        project_structure = self.files_parser.invoke(source_dir)
        classes = self.layer_classifier.invoke(project_structure) 

        assert list(project_structure.keys()) == list(classes.keys()), "The project structure and classes should be the same size."

        # TODO: Run python scripts


if __name__ == "__main__":
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="Qwen/Qwen2.5-Coder-32B-Instruct",
        api_key="U3NKiHbEzT2Fcqyb0X5OWQyTFDIcFQbV",
        base_url="https://api.deepinfra.com/v1/openai",
    )

    reviewer = CodeReviewer(FilesParser(), LayerClassifier(llm))
    print(reviewer.invoke(DATA_PATH))