import ast
from pathlib import Path


def test_no_shell_true():
    render_dir = Path("src/scene_signal/render")
    for py_file in render_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "shell=True" not in content, f"Found shell=True in {py_file}"

def test_cross_module_isolation():
    render_dir = Path("src/scene_signal/render")
    for py_file in render_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("scene_signal.adapters") or "render" in alias.name, f"Cross-module import in {py_file}: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("scene_signal"):
                    assert "render" in node.module, f"Cross-module import from Module 01 in {py_file}: {node.module}"
