from pathlib import Path
import os


# DATA_PATH = Path(__file__).parent.parent
DATA_PATH = r"D:\ITMO\hacks\llm_review\python\backend-master"


class FilesParser:
    def _collect_settings_structure(self, source_dir, extension: str = ".py"):
        project_structure = {}

        for root, _, files in os.walk(source_dir):
            root_dir = Path(root).relative_to(source_dir)

            py_files = [f for f in files if f.endswith(extension)]
            if py_files:
                project_structure[root_dir] = py_files

        return project_structure

    def invoke(self, source_dir: Path, extension: str = ".py"):
        files_structure = self._collect_settings_structure(source_dir=source_dir, extension=extension)
        return files_structure


if __name__ == "__main__":
    parser = FilesParser()
    result = parser.invoke(DATA_PATH)
    print(result)
