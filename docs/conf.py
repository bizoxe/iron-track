"""Sphinx configuration."""

from __future__ import annotations

import importlib.metadata
import warnings
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
)

from sqlalchemy.exc import SAWarning

if TYPE_CHECKING:
    from sphinx.addnodes import document
    from sphinx.application import Sphinx

warnings.filterwarnings("ignore", category=SAWarning)

# -- Project information --------------------------------------
project = importlib.metadata.metadata("irontrack")["Name"]
copyright = "2025, Alexander Matveev"
author = "Alex Matveev"
release = importlib.metadata.version("irontrack")

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx_click",
    "sphinxcontrib.typer",
    "sphinx_design",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinxcontrib.autodoc_pydantic",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
    "sphinx.ext.intersphinx",
    "sphinx_toolbox.collapse",
    "sphinx.ext.autosectionlabel",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "anyio": ("https://anyio.readthedocs.io/en/stable/", None),
    "click": ("https://click.palletsprojects.com/en/8.1.x/", None),
    "structlog": ("https://www.structlog.org/en/stable/", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
    "msgspec": ("https://jcristharif.com/msgspec/", None),
    "advanced-alchemy": ("https://docs.advanced-alchemy.litestar.dev/latest/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# -- Napoleon configuration --------------------------------
napoleon_google_docstring = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_attr_annotations = True

# -- Autodoc configuration ----------------------------------------------------
autoclass_content = "class"
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "exclude-members": "__weakref__, __init__, model_post_init",
    "show-inheritance": True,
    "class-signature": "separated",
    "typehints-format": "short",
}

autodoc_typehints = "none"
autosectionlabel_prefix_document = True
autodoc_preserve_defaults = False
suppress_warnings = [
    "autosectionlabel.*",
]
todo_include_todos = True

# -- Autodoc Pydantic configuration -------------------------------------------
autodoc_pydantic_model_members = True
autodoc_pydantic_model_show_paramlist = False
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_config_members = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_model_members = True
autodoc_pydantic_settings_show_validator_members = False
autodoc_pydantic_model_show_field_summary = True
autodoc_pydantic_model_show_field_list = True
autodoc_pydantic_field_swap_cleared_annotated_with_original_type = True
autodoc_pydantic_model_show_validator_summary = True

# -- Style configuration -----------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]
html_show_sourcelink = True
html_title = "IronTrack Docs"
html_context = {
    "github_user": "bizoxe",
    "github_repo": "iron-track",
    "github_version": "main",
    "doc_path": "docs",
}

# -- Autodoc Hooks ---------------------------------------------
EXCLUDED_ORM_MEMBERS = {
    "metadata",
    "registry",
    "awaitable_attrs",
    "to_dict",
}


def autodoc_skip_member_hook(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    skip: bool,
    options: Any,
) -> bool:
    if what in ("class", "attribute", "method") and name in EXCLUDED_ORM_MEMBERS:
        return True

    return skip


def update_html_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: document,
) -> None:
    if "generate_toctree_html" in context:
        context["generate_toctree_html"] = partial(context["generate_toctree_html"], startdepth=0)


def setup(app: Sphinx) -> dict[str, bool]:
    app.setup_extension("shibuya")
    app.connect("html-page-context", update_html_context)
    app.connect("autodoc-skip-member", autodoc_skip_member_hook)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
