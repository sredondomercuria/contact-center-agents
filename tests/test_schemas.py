"""Los JSON Schemas deben ser válidos para structured outputs."""

from __future__ import annotations

import pytest

from contact_center import schemas

ALL = [
    schemas.TRIAGE_SCHEMA, schemas.QUERY_SCHEMA, schemas.RESPONSE_SCHEMA,
    schemas.REVIEW_SCHEMA, schemas.ROUTING_SCHEMA,
]


def _check(node: dict) -> None:
    assert node["type"] == "object"
    assert node.get("additionalProperties") is False
    props = node["properties"]
    for req in node.get("required", []):
        assert req in props
    for v in props.values():
        if v.get("type") == "object":
            _check(v)
        if v.get("type") == "array" and v["items"].get("type") == "object":
            _check(v["items"])


@pytest.mark.parametrize("schema", ALL)
def test_schema_well_formed(schema):
    _check(schema)
