"""Sphinx configuration."""

from __future__ import annotations

import importlib.metadata
import re
import warnings
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import SAWarning

from app.config import constants

if TYPE_CHECKING:
    from docutils.nodes import document
    from sphinx.application import Sphinx

warnings.filterwarnings("ignore", category=SAWarning)

# --- Global variables for documentation (rst_prolog) ---
rst_prolog = f"""
.. |ARGON2_TIME_COST| replace:: {constants.ARGON2_TIME_COST}
.. |ARGON2_MEMORY_COST| replace:: {constants.ARGON2_MEMORY_COST}
.. |ARGON2_PARALLELISM| replace:: {constants.ARGON2_PARALLELISM}
"""

# -- Project information --------------------------------------
current_year = datetime.now().year  # noqa: DTZ005
project = importlib.metadata.metadata("irontrack")["Name"]
copyright = f"{current_year}, Alexander Matveev"
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

default_role = "code"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "anyio": ("https://anyio.readthedocs.io/en/stable/", None),
    "click": ("https://click.palletsprojects.com/en/stable/", None),
    "structlog": ("https://www.structlog.org/en/stable/", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
    "advanced-alchemy": ("https://advanced-alchemy.litestar.dev/latest/", None),
    "pydantic": ("https://pydantic.dev/docs/validation/latest/", None),
    "msgspec": ("https://msgspec.dev", None),
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
autodoc_typehints = "signature"
autosectionlabel_prefix_document = True
autodoc_preserve_defaults = False
python_use_unqualified_type_names = True
add_module_names = False
suppress_warnings = [
    "autosectionlabel.*",
]
todo_include_todos = True

# -- Viewcode configuration -------------------------------------------
viewcode_follow_imported_members = False

# -- Autodoc Pydantic configuration -------------------------------------------
autodoc_pydantic_model_signature_prefix = "class"
autodoc_pydantic_model_members = True
autodoc_pydantic_model_hide_paramlist = True
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_validator_summary = True
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_settings_show_validator_members = False

# -- Style configuration -----------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]
html_logo = "_static/logo.svg"
html_theme_options = {
    "github_url": "https://github.com/bizoxe/iron-track",
    "nav_links": [
        {"title": "Installation", "url": "usage/installation"},
        {"title": "API Reference", "url": "api/index"},
    ],
}
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


def simplify_annotated(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: dict[str, Any],
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str | None, str | None]:
    """Drop `Annotated` metadata and `~` prefixes from signatures."""
    if signature:
        signature = replace_annotated(signature).replace("~", "")
    if return_annotation:
        return_annotation = return_annotation.replace("~", "")

    return signature, return_annotation


# -- Annotated Typehint Cleanup -----------------------------------------------
# Shared helpers for simplify_annotated (signatures) and the pydantic field
# patch below (field `:type:` lines).
ANNOTATED_START_RE = re.compile(r"^(?:~?typing\.)?Annotated\[")
ANNOTATED_OCCURRENCE_RE = re.compile(r"(?:~?typing\.)?Annotated\[")
FIELD_META_RE = re.compile(r"^(?:~?(?:pydantic\.)?)(?:FieldInfo|Field)\(.*\)$", re.DOTALL)
FIELD_TYPE_LINE_RE = re.compile(r"^(\s*:type:\s)(.*)$", re.DOTALL)


def find_closing_bracket(text: str, open_idx: int) -> int | None:
    depth = 0
    for idx in range(open_idx, len(text)):
        if text[idx] in "[({":
            depth += 1
        elif text[idx] in "])}":
            depth -= 1
            if depth == 0:
                return idx
    return None


def split_annotated_elements(annotation: str) -> list[str] | None:
    """Split an `Annotated[...]` typehint into its top-level elements.

    Returns None unless the string is a plain `Annotated[...]`. Brackets
    are balanced by scanning: metadata reprs may contain dict and call
    literals that regular expressions cannot split reliably.
    """
    if not ANNOTATED_START_RE.match(annotation):
        return None

    open_idx = annotation.index("[")
    close_idx = find_closing_bracket(annotation, open_idx)
    if close_idx != len(annotation) - 1:
        return None

    body = annotation[open_idx + 1 : close_idx]
    elements: list[str] = []
    depth = 0
    start = 0
    for pos, char in enumerate(body):
        if char in "[({":
            depth += 1
        elif char in "])}":
            depth -= 1
        elif char == "," and depth == 0:
            elements.append(body[start:pos].strip())
            start = pos + 1
    elements.append(body[start:].strip())
    return elements


def replace_annotated(signature: str) -> str:
    """Replace every `Annotated[...]` in a signature with its base type.

    A `re.sub` alternative cannot balance brackets: with several annotated
    parameters a greedy `.*]` match swallows everything up to the last
    bracket of the signature and drops the trailing parameters.
    """
    parts: list[str] = []
    pos = 0
    while match := ANNOTATED_OCCURRENCE_RE.search(signature, pos):
        parts.append(signature[pos : match.start()])
        end = find_closing_bracket(signature, match.end() - 1)
        if end is None:
            return signature

        chunk = signature[match.start() : end + 1]
        elements = split_annotated_elements(chunk)
        parts.append(elements[0] if elements else chunk)
        pos = end + 1
    parts.append(signature[pos:])
    return "".join(parts)


def strip_annotated_metadata(annotation: str) -> str:
    """Drop `Field`/`FieldInfo` metadata from an `Annotated[...]` hint.

    Sphinx expands `Annotated[T, Field(...)]` to the full metadata repr and
    truncates on dict literals inside it (`examples=[{'reason': ...}]`
    renders as garbage). Named validators are kept as part of the field
    contract; descriptions and examples still render in the field body from
    the `FieldInfo` object, while constraints render when `field-show-constraints`
    is enabled.
    """
    elements = split_annotated_elements(annotation)
    if elements is None:
        return annotation

    remaining = [element for element in elements if not FIELD_META_RE.match(element)]
    if not remaining:
        return annotation
    if len(remaining) == 1:
        return remaining[0]
    return f"Annotated[{', '.join(remaining)}]"


def clean_field_type_line(line: str) -> str:
    """Strip `Annotated` metadata from a `:type:` line of a pydantic field."""
    match = FIELD_TYPE_LINE_RE.match(line)
    if not match:
        return line

    prefix, annotation = match.groups()
    if "Annotated[" not in annotation:
        return line

    return f"{prefix}{strip_annotated_metadata(annotation.strip())}"


def patch_pydantic_field_documenter() -> None:
    """Wrap `PydanticFieldDocumenter.add_line` to clean `:type:` lines.

    Idempotent to stay safe across repeated configuration loads.
    """
    from sphinxcontrib.autodoc_pydantic.directives.autodocumenters import (
        PydanticFieldDocumenter,
    )

    if getattr(PydanticFieldDocumenter.add_line, "_annotated_stripped", False):
        return

    orig_add_line = PydanticFieldDocumenter.add_line

    def add_line(self: PydanticFieldDocumenter, line: str, source: str, *lineno: int) -> None:
        orig_add_line(self, clean_field_type_line(line), source, *lineno)

    add_line._annotated_stripped = True  # type: ignore[attr-defined]
    PydanticFieldDocumenter.add_line = add_line


patch_pydantic_field_documenter()


# -- Theme Hook and Application Setup -----------------------------------------
def update_html_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: document,
) -> None:
    """Include the root toctree level in the sidebar navigation."""
    if "generate_toctree_html" in context:
        context["generate_toctree_html"] = partial(context["generate_toctree_html"], startdepth=0)


def setup(app: Sphinx) -> dict[str, bool]:
    app.setup_extension("shibuya")
    app.connect("html-page-context", update_html_context)
    app.connect("autodoc-skip-member", autodoc_skip_member_hook)
    app.connect("autodoc-process-signature", simplify_annotated)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
