"""Chính sách dự án là 1 tệp; tài liệu văn xuôi không bị biến thành 'từ cấm'; render luôn tuân thủ chính sách."""
from __future__ import annotations

import asyncio
import uuid

from socnhotv.core.contracts.types import Edge, Graph, GraphRunRequest, NodeInstance, RunMode
from socnhotv.core.engine import content_policy as cp
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.storage.project_store import ProjectStore

NOW = "2026-11-06T00:00:00Z"

PROSE = "\n".join(
    ["# YouTube Channel Monetisation Policies", "## Reused content"]
    + [
        "Content that is mass produced or repetitive may not be eligible for monetisation because viewers expect original value."
    ]
    * 60
)


def test_prose_policy_is_a_document_not_a_term_list(tmp_path):
    assert cp.looks_like_prose(PROSE)
    assert not cp.looks_like_prose("# Bạo lực\nsúng, dao\n# Chửi thề\nđm, vl\n" * 400)

    proj = tmp_path / "data" / "projects" / "p1"
    proj.mkdir(parents=True)
    (proj / "project.json").write_text("{}", encoding="utf-8")
    doc = cp.add_document(tmp_path, "p1", "chính sách youtube.md", PROSE)
    assert doc["file"].startswith("policy/") and doc["sections"][:2] == ["YouTube Channel Monetisation Policies", "Reused content"]
    assert (proj / doc["file"]).read_text(encoding="utf-8") == PROSE
    pol = cp.load_policy(tmp_path, "p1")
    assert [d["id"] for d in pol["documents"]] == [doc["id"]]
    # nhập lại cùng tệp: ghi đè, không nhân đôi
    cp.add_document(tmp_path, "p1", "chính sách youtube.md", PROSE + "\nthêm")
    assert len(cp.load_policy(tmp_path, "p1")["documents"]) == 1
    assert "Reused content" in cp.read_documents(tmp_path, "p1", cp.load_policy(tmp_path, "p1"))


def test_render_enforces_project_policy_even_without_quality_node():
    async def _t():
        runner = GraphRunner(ProjectStore("soc-nho-tv"))

        def graph(text):
            return Graph(
                id=f"test_enf_{uuid.uuid4().hex[:6]}",
                project_id="soc-nho-tv",
                nodes=[
                    NodeInstance(id="s", type="script", params={"mode": "paste", "rawScript": text, "targetSceneCount": 2}),
                    NodeInstance(id="r", type="hyperframes_render", params={"aspectRatio": "16:9"}),
                ],
                edges=[Edge(id="e", source_node_id="s", source_port="scenes", target_node_id="r", target_port="scenes")],
                updated_at=NOW,
            )

        bad = await runner.run(
            graph("Sóc Bi: Mình sẽ đánh nhau và đổ máu!"),
            GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, mock_mode=True, max_retries=1),
        )
        assert "r" in bad.failed_nodes and "Chính sách nội dung" in bad.errors["r"]

    asyncio.run(_t())
