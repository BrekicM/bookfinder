"""The app's static and template directories must not depend on the CWD.

Anchoring them on the package means an installed copy — or a process started
from anywhere but the repo root — still finds its own assets.
"""

import importlib
import sys
from pathlib import Path

import pytest

import book_finder


@pytest.fixture
def isolated_import(monkeypatch, tmp_path):
    """Import book_finder modules afresh from a working directory that is not the repo root."""
    saved = {name: mod for name, mod in sys.modules.items() if name.startswith("book_finder")}
    for name in saved:
        del sys.modules[name]
    monkeypatch.chdir(tmp_path)
    try:
        yield importlib.import_module
    finally:
        sys.modules.update(saved)


def test_app_imports_from_a_foreign_working_directory(isolated_import) -> None:
    main = isolated_import("book_finder.main")

    assert main.app is not None


def test_template_directory_is_anchored_on_the_package(isolated_import) -> None:
    render = isolated_import("book_finder.web.render")

    searchpath = Path(render.templates.env.loader.searchpath[0])
    package_templates = Path(book_finder.__file__).parent / "web" / "templates"
    assert searchpath.is_absolute()
    assert searchpath == package_templates
