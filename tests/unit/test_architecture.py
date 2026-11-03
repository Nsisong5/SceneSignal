"""Architecture tests enforcing dependency rules and stdlib shadowing guards."""

import ast
import sys
from pathlib import Path


def test_stdlib_shadowing():
    """Ensure no module file under src/scene_signal is named like a stdlib top-level module."""
    package_dir = Path("src/scene_signal")
    stdlib_names = sys.stdlib_module_names
    for path in package_dir.glob("**/*.py"):
        module_name = path.stem
        if module_name == "__init__":
            continue
        assert module_name not in stdlib_names, (
            f"Module '{path}' is named '{module_name}', which shadows a Python standard library module."
        )


def test_domain_application_port_dependencies():
    """Enforce that domain, application, and ports layers do not import forbidden modules."""
    package_dir = Path("src/scene_signal")
    forbidden_substrings = [
        "fastapi",
        "uvicorn",
        "httpx",
        "adapters",
        "openai",
        "anthropic",
        "google",
        "boto3",
    ]

    restricted_layers = ["domain", "application", "ports"]
    for layer in restricted_layers:
        layer_path = package_dir / layer
        if not layer_path.exists():
            continue
        for path in layer_path.glob("**/*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        full_import = name.name
                        for forbidden in forbidden_substrings:
                            assert forbidden not in full_import.lower(), (
                                f"Architectural violation in {path}: layer '{layer}' imports forbidden module '{full_import}' (matched '{forbidden}')."
                            )
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        full_import = f"{module}.{name.name}" if module else name.name
                        for forbidden in forbidden_substrings:
                            assert forbidden not in full_import.lower(), (
                                f"Architectural violation in {path}: layer '{layer}' imports forbidden module '{full_import}' (matched '{forbidden}')."
                            )
