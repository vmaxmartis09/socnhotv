from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from socnhotv.core.contracts.types import (
    Graph,
    GraphValidationResult,
    NodeInstance,
    is_port_compatible,
)
from socnhotv.core.nodes.registry import NodeRegistry


def validate_graph(graph: Graph) -> GraphValidationResult:
    """Kiểm tra toàn diện tính hợp lệ của đồ thị node:
    1. Kiểm tra tính duy nhất của Node ID và tính hợp lệ của Node Type.
    2. Kiểm tra tính hợp lệ của Edge (node tồn tại, cổng tồn tại, tương thích kiểu cổng).
    3. Phát hiện chu trình (Cycle Detection).
    4. Xác định thứ tự thực thi topo (Topological Sort).
    5. Kiểm tra các cổng đầu vào bắt buộc (Required Inputs).
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Đảm bảo NodeRegistry có sẵn định nghĩa
    if not NodeRegistry.list_all():
        NodeRegistry.initialize_defaults()

    # 1. Kiểm tra Node IDs và Types
    node_map: Dict[str, NodeInstance] = {}
    for node in graph.nodes:
        if node.id in node_map:
            errors.append(f"Trùng lặp mã Node ID '{node.id}' trong đồ thị.")
            continue
        node_map[node.id] = node

        node_def = NodeRegistry.get(node.type)
        if not node_def:
            errors.append(f"Loại node '{node.type}' tại node '{node.id}' không có trong NodeRegistry.")

    # 2. Xây dựng cấu trúc đồ thị và kiểm tra Edge
    adj: Dict[str, List[str]] = {nid: [] for nid in node_map}
    in_degree: Dict[str, int] = {nid: 0 for nid in node_map}
    connected_target_ports: Set[Tuple[str, str]] = set()

    for edge in graph.edges:
        src_id = edge.source_node_id
        tgt_id = edge.target_node_id

        if src_id not in node_map:
            errors.append(f"Dây nối '{edge.id}' trỏ từ node không tồn tại '{src_id}'.")
            continue
        if tgt_id not in node_map:
            errors.append(f"Dây nối '{edge.id}' trỏ tới node không tồn tại '{tgt_id}'.")
            continue

        src_node = node_map[src_id]
        tgt_node = node_map[tgt_id]

        src_def = NodeRegistry.get(src_node.type)
        tgt_def = NodeRegistry.get(tgt_node.type)

        if not src_def or not tgt_def:
            continue

        # Tìm định nghĩa cổng ra và cổng vào (có tính cổng tuỳ biến của từng node)
        _, src_outs = NodeRegistry.effective_ports(src_node.type, src_node.params)
        tgt_ins, _ = NodeRegistry.effective_ports(tgt_node.type, tgt_node.params)
        src_port = next((p for p in src_outs if p.name == edge.source_port), None)
        tgt_port = next((p for p in tgt_ins if p.name == edge.target_port), None)

        if not src_port:
            errors.append(
                f"Node '{src_id}' ({src_node.type}) không có cổng ra tên '{edge.source_port}'."
                + _disabled_capability_hint(src_node, edge.source_port, output=True)
            )
        if not tgt_port:
            errors.append(
                f"Node '{tgt_id}' ({tgt_node.type}) không có cổng vào tên '{edge.target_port}'."
                + _disabled_capability_hint(tgt_node, edge.target_port, output=False)
            )

        if src_port and tgt_port:
            if not is_port_compatible(src_port.port_type, tgt_port.port_type):
                errors.append(
                    f"Không tương thích kiểu cổng: Dây nối '{edge.id}' từ cổng ra '{edge.source_port}' "
                    f"({src_port.port_type.value}) của node '{src_id}' không thể nối vào cổng vào "
                    f"'{edge.target_port}' ({tgt_port.port_type.value}) của node '{tgt_id}'."
                )

        adj[src_id].append(tgt_id)
        in_degree[tgt_id] += 1
        connected_target_ports.add((tgt_id, edge.target_port))

    # Đồng bộ cả các kết nối được định nghĩa trong node.inputs (nếu có NodePortInputRef)
    for tgt_id, tgt_node in node_map.items():
        for port_name, input_val in tgt_node.inputs.items():
            if isinstance(input_val, dict) and "nodeId" in input_val:
                src_id = input_val["nodeId"]
                src_port_name = input_val.get("outputPort", "")
                if src_id in node_map:
                    # Kiểm tra xem edge đã có chưa để tránh tính trùng
                    has_edge = any(
                        e.source_node_id == src_id
                        and e.target_node_id == tgt_id
                        and e.target_port == port_name
                        for e in graph.edges
                    )
                    if not has_edge:
                        adj[src_id].append(tgt_id)
                        in_degree[tgt_id] += 1
                        connected_target_ports.add((tgt_id, port_name))

    # 3. Thuật toán Kahn: Cycle Detection & Topological Sort
    # Tạo bản sao in_degree để duyệt
    working_in_degree = dict(in_degree)
    queue: List[str] = [nid for nid, deg in working_in_degree.items() if deg == 0]
    topological_order: List[str] = []

    while queue:
        u = queue.pop(0)
        topological_order.append(u)
        for v in adj.get(u, []):
            working_in_degree[v] -= 1
            if working_in_degree[v] == 0:
                queue.append(v)

    if len(topological_order) != len(node_map):
        cycle_nodes = [nid for nid, deg in working_in_degree.items() if deg > 0]
        errors.append(
            f"Phát hiện chu trình (vòng lặp vô hạn) trong đồ thị liên quan đến các node: {sorted(cycle_nodes)}. "
            "Đồ thị phải là DAG (Directed Acyclic Graph) để có thể thực thi."
        )
        topological_order = []

    # 4. Kiểm tra Required Inputs và tính đầy đủ của dữ liệu nhập liệu trên card
    for node_id, node in node_map.items():
        node_def = NodeRegistry.get(node.type)
        if not node_def:
            continue

        # Kiểm tra chi tiết cho các node nhập liệu cốt lõi
        if node.type == "script":
            mode = str(node.params.get("mode", "ai"))
            if mode == "episode":
                if not str(node.params.get("episodeId", "")).strip():
                    warnings.append(
                        f"Node '{node_id}' (script) đang ở chế độ 'Kịch bản tập' nhưng chưa chọn tập (episodeId rỗng)."
                    )
            elif mode == "paste":
                raw_s = str(node.params.get("rawScript", "")).strip()
                if not raw_s:
                    warnings.append(
                        f"Node '{node_id}' (script) đang ở chế độ 'Dán kịch bản' nhưng chưa dán kịch bản (rawScript rỗng)."
                    )
            else:
                is_connected = (node_id, "text") in connected_target_ports
                has_text = bool(str(node.params.get("text") or node.params.get("content", "")).strip())
                if not (is_connected or has_text):
                    warnings.append(
                        f"Node '{node_id}' (script) chưa nhận ý tưởng (cổng 'text' chưa nối và chưa nhập text)."
                    )

        elif node.type == "voice_tts":
            is_connected = (node_id, "text") in connected_target_ports
            has_text = bool(str(node.params.get("text", "")).strip())
            if not (is_connected or has_text):
                warnings.append(
                    f"Node '{node_id}' (voice_tts) chưa nhận lời thoại cần đọc (cổng 'text' chưa nối và chưa nhập text)."
                )

        elif node.type in ("image", "character_image"):
            uri = str(node.params.get("uri", "")).strip()
            if not uri:
                warnings.append(
                    f"Node '{node_id}' ({node.type}) chưa có ảnh được chọn hoặc tải lên (uri rỗng)."
                )

        # Chức năng bật/tắt: chỉ cho bật chức năng đã có bộ chạy
        for cap in NodeRegistry.enabled_capabilities(node.type, node.params):
            from socnhotv.core.nodes.capabilities import get_runtime

            if not cap.available or get_runtime(node.type, cap.name) is None:
                errors.append(
                    f"Node '{node_id}' ({node.type}) đang bật chức năng '{cap.display_name}' nhưng chức năng này chưa sẵn sàng."
                )

        eff_ins, _ = NodeRegistry.effective_ports(node.type, node.params)
        for req_port in eff_ins:
            if not req_port.required:
                continue
            is_connected = (node_id, req_port.name) in connected_target_ports
            has_input_literal = req_port.name in node.inputs and node.inputs[req_port.name] is not None
            has_param_literal = (req_port.name in node.params and node.params[req_port.name] is not None) or (
                req_port.default_value not in (None, "")
            )

            if not (is_connected or has_input_literal or has_param_literal):
                warnings.append(
                    f"Node '{node_id}' ({node.type}) chưa nhận dữ liệu cho cổng bắt buộc '{req_port.name}'."
                )

    is_valid = len(errors) == 0
    return GraphValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        topological_order=topological_order,
    )


def _disabled_capability_hint(node, port_name: str, output: bool) -> str:
    """Gợi ý khi dây nối vào cổng của một chức năng đang tắt (dây không bị xoá, chỉ báo rõ)."""
    for cap in NodeRegistry.capabilities_of(node.type):
        ports = cap.output_ports if output else cap.input_ports
        if any(p.name == port_name for p in ports) and not NodeRegistry.is_capability_enabled(node.params, cap.name):
            return f" Cổng này thuộc chức năng '{cap.display_name}' đang tắt: bật lại chức năng hoặc gỡ dây."
    return ""
