from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.service import OffsetPagination

if TYPE_CHECKING:
    import msgspec


def response_spec(
    schema: type[msgspec.Struct],
    description: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema.__name__}"}}},
    }
    if description is not None:
        payload["description"] = description
    return payload


def response_spec_paginated(schema: type[msgspec.Struct]) -> dict[str, Any]:
    schema_name = f"{OffsetPagination.__name__}_{schema.__name__}_"
    payload: dict[str, Any] = {
        "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema_name}"}}},
    }
    return payload


def response_spec_list(schema: type[msgspec.Struct]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "content": {
            "application/json": {
                "schema": {
                    "type": "array",
                    "items": {"$ref": f"#/components/schemas/{schema.__name__}"},
                }
            }
        },
    }
    return payload
