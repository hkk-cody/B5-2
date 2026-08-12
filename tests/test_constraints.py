"""과제에서 금지한 API와 외부 그래프 라이브러리 사용을 검사합니다."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def implementation_files() -> list[Path]:
    """테스트를 제외한 실제 프로그램 Python 파일을 반환합니다."""

    return [PROJECT_ROOT / "main.py", *(PROJECT_ROOT / "minigit").rglob("*.py")]


class AssignmentConstraintTests(unittest.TestCase):
    def test_implementation_does_not_use_builtin_sorting_apis(self) -> None:
        violations: list[str] = []

        for path in implementation_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == "sorted":
                    violations.append(f"{path.name}:{node.lineno} sorted")
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"sort", "sorted"}
                ):
                    violations.append(
                        f"{path.name}:{node.lineno} .{node.func.attr}()"
                    )
                if isinstance(node, ast.ImportFrom) and node.module == "builtins":
                    for alias in node.names:
                        if alias.name == "sorted":
                            violations.append(f"{path.name}:{node.lineno} sorted import")

        self.assertEqual(
            violations,
            [],
            "금지된 정렬 API 사용: " + ", ".join(violations),
        )

    def test_implementation_does_not_import_graph_libraries(self) -> None:
        banned_modules = {"networkx", "igraph"}
        violations: list[str] = []

        for path in implementation_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                module_names: list[str] = []
                if isinstance(node, ast.Import):
                    module_names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    module_names = [node.module]

                for module_name in module_names:
                    root_module = module_name.split(".", maxsplit=1)[0]
                    if root_module in banned_modules:
                        violations.append(f"{path.name}:{node.lineno} {module_name}")

        self.assertEqual(
            violations,
            [],
            "금지된 그래프 라이브러리 사용: " + ", ".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
