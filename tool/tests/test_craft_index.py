"""Unit test for video craft techniques indexer and schema validation."""
from pathlib import Path
import sys

# Ensure tool directory and workspace root are in sys.path
workspace_root = Path(__file__).resolve().parents[2]
tool_dir = workspace_root / "tool"
for p in (str(workspace_root), str(tool_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.video_craft_index import scan_all_cards, validate_card, generate_registry

def test_all_techniques_have_valid_frontmatter():
    cards, errors = scan_all_cards()
    assert len(errors) == 0, f"Validation errors found: {errors}"
    assert len(cards) >= 26, f"Expected at least 26 technique cards, found {len(cards)}"

def test_registry_generation():
    cards, errors = scan_all_cards()
    assert not errors
    registry = generate_registry(cards)
    assert registry["total_cards"] >= 26
    assert registry["in_studio_count"] >= 5
    assert "confession-hook" in registry["techniques"]
    assert "foreground-occlusion-spatial-depth-layering" in registry["techniques"]
    assert "transition-foresight-continuity" in registry["techniques"]
