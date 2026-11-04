"""Unit test for video craft card promotion and lifecycle management."""
from pathlib import Path
import sys

_curr = Path(__file__).resolve()
workspace_root = _curr.parents[2]
tool_dir = workspace_root / "tool"
for p in (str(workspace_root), str(tool_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.video_craft_promote import check_expirations

def test_check_expirations():
    expired_count = check_expirations()
    # Currently all 26 cards are active/never or set to 2027
    assert expired_count == 0
