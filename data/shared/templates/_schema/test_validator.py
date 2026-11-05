from __future__ import annotations

from pathlib import Path
import pytest

from data.shared.templates._schema.validator import (
    validate_all_templates,
    validate_template_dict,
    validate_template_file,
)


def test_validator_all_eight_templates():
    templates_root = Path(__file__).resolve().parent.parent
    results = validate_all_templates(templates_root)
    assert len(results) == 8, f"Expected 8 templates, found {len(results)}"

    for name, (errs, warns) in results.items():
        assert len(errs) == 0, f"Template {name} failed validation: {errs}"


def test_validator_rejects_missing_required():
    fake = {"id": "test", "name": "Test"}
    errs, _ = validate_template_dict(fake)
    assert len(errs) > 0
    missing_fields = {e.field for e in errs}
    assert "kind" in missing_fields
    assert "status" in missing_fields
    assert "tier" in missing_fields
    assert "requires" in missing_fields
    assert "recipe" in missing_fields
    assert "slots" in missing_fields
    assert "outputs" in missing_fields


def test_validator_rejects_unverified_claiming_verified():
    fake = {
        "id": "test-unverified",
        "name": "Test Unverified",
        "version": 2,
        "kind": "review",
        "category": "review",
        "status": "verified",
        "tier": "A",
        "requires": {"tools": [], "providers": [], "gpu": False, "ffmpeg": True},
        "recipe": {"nodes": ["text"]},
        "slots": [{"key": "title", "type": "text"}],
        "outputs": {"aspect": ["9:16"]},
    }
    errs, _ = validate_template_dict(fake)
    err_msgs = [e.message for e in errs]
    assert any("sample_output" in msg for msg in err_msgs)
    assert any("verified_on" in msg for msg in err_msgs)
