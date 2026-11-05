from socnhotv.core.contracts.types import Graph, NodeInstance, Edge
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.nodes.registry import NodeRegistry


def test_effective_ports_override_and_validate():
    NodeRegistry.initialize_defaults()
    ins, outs = NodeRegistry.effective_ports("image_gen", {})
    assert [p.name for p in ins] == ["prompt", "references"]

    params = {
        "_ports": {
            "inputs": [{"name": "prompt_phu", "portType": "text", "required": False, "mapTo": "prompt"}],
            "outputs": [{"name": "anh_chinh", "portType": "image", "mapTo": "image"}],
        }
    }
    ins, outs = NodeRegistry.effective_ports("image_gen", params)
    assert ins[0].name == "prompt_phu" and ins[0].map_to == "prompt"
    assert outs[0].name == "anh_chinh"

    g = Graph(
        id="g1",
        project_id="p1",
        nodes=[
            NodeInstance(id="a", type="text", params={"content": "x"}),
            NodeInstance(id="b", type="image_gen", params=params),
        ],
        edges=[Edge(id="e", source_node_id="a", source_port="text", target_node_id="b", target_port="prompt_phu")],
    )
    res = validate_graph(g)
    assert res.is_valid, res.errors
