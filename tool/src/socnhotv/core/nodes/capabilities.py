"""Chức năng bật/tắt được gắn trong một node (capability).

Ví dụ: node Nhân vật có chức năng "Nói" (đọc lời thoại của chính nhân vật) và "Ảnh theo cảnh".
Mỗi chức năng gồm:
- phần khai báo (`CapabilityDefinition`): cổng vào/ra, tham số mặc định. Gắn vào NodeDefinition.capabilities,
  được trả qua GET /node-types để giao diện hiện cổng khi bật.
- phần chạy (`CapabilityRuntime`): tự tính khoá cache, ước tính chi phí và chạy.

Bật chức năng: params[<tên>] = {"enabled": True, ...tham số riêng}.
Bộ chạy chạy phần lõi của node trước, rồi lần lượt từng chức năng đang bật. Chức năng nào có khoá cache
không đổi thì lấy lại kết quả cũ, không gọi provider lần nữa.
"""
from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from socnhotv.core.contracts.types import CapabilityDefinition, NodeInstance
from socnhotv.core.nodes.registry import NodeRegistry

if TYPE_CHECKING:  # pragma: no cover
    from socnhotv.core.engine.graph_runner import GraphRunner


class CapabilityRuntime:
    """Phần chạy của một chức năng. Lớp con ghi đè `run` (bắt buộc), `estimate_cost`, `cache_inputs` (tuỳ chọn)."""

    def cache_inputs(
        self,
        node: NodeInstance,
        resolved_inputs: Dict[str, Any],
        definition: CapabilityDefinition,
        core_outputs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Dữ liệu vào ảnh hưởng tới kết quả. Mặc định: giá trị các cổng vào của chức năng.

        `core_outputs` = kết quả phần lõi của node (vd. hồ sơ nhân vật có voiceId) để đưa vào khoá cache.
        """
        return {p.name: resolved_inputs.get(p.name) for p in definition.input_ports}

    def estimate_cost(
        self, node: NodeInstance, params: Dict[str, Any], runner: "GraphRunner", real_mode: bool
    ) -> float:
        return 0.0

    async def run(
        self,
        runner: "GraphRunner",
        node: NodeInstance,
        params: Dict[str, Any],
        resolved_inputs: Dict[str, Any],
        core_outputs: Dict[str, Any],
        run_id: str,
        is_mock: bool,
    ) -> Tuple[Dict[str, Any], float]:
        raise NotImplementedError


_RUNTIMES: Dict[Tuple[str, str], CapabilityRuntime] = {}


def register_capability(
    node_type: str, definition: CapabilityDefinition, runtime: Optional[CapabilityRuntime] = None
) -> None:
    """Gắn chức năng vào một loại node (ghi đè nếu trùng tên)."""
    NodeRegistry.add_capability(node_type, definition)
    if runtime is not None:
        _RUNTIMES[(node_type, definition.name)] = runtime
    else:
        _RUNTIMES.pop((node_type, definition.name), None)


def unregister_capability(node_type: str, name: str) -> None:
    NodeRegistry.remove_capability(node_type, name)
    _RUNTIMES.pop((node_type, name), None)


def get_runtime(node_type: str, name: str) -> Optional[CapabilityRuntime]:
    rt = _RUNTIMES.get((node_type, name))
    if rt is None:
        base = NodeRegistry.get(node_type)
        if base is not None and base.base_type:
            rt = _RUNTIMES.get((base.base_type, name))
    return rt


def capability_params(definition: CapabilityDefinition, params: Optional[dict]) -> Dict[str, Any]:
    """Tham số hiệu lực của chức năng = mặc định + params[<tên>]."""
    own = (params or {}).get(definition.name)
    merged = dict(definition.default_params or {})
    if isinstance(own, dict):
        merged.update(own)
    return merged


def enabled_capabilities(node_type: str, params: Optional[dict]) -> List[CapabilityDefinition]:
    return NodeRegistry.enabled_capabilities(node_type, params)


def capability_cache_key(
    node: NodeInstance,
    definition: CapabilityDefinition,
    params: Dict[str, Any],
    inputs: Any,
    is_mock: bool,
) -> str:
    """Khoá cache: loại node + tên chức năng + tham số chức năng + dữ liệu vào + chế độ mock/thật.

    Artifact rút gọn về id (đã theo mã băm nội dung) để cùng nội dung thì cùng khoá.
    """

    def _norm(v: Any) -> Any:
        art_id = getattr(v, "id", None)
        if art_id is not None and hasattr(v, "uri") and hasattr(v, "kind"):
            return f"art:{art_id}"
        if isinstance(v, dict):
            return {str(k): _norm(x) for k, x in sorted(v.items(), key=lambda kv: str(kv[0]))}
        if isinstance(v, (list, tuple)):
            return [_norm(x) for x in v]
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    raw = json.dumps(
        {
            "type": node.type,
            "cap": definition.name,
            "params": _norm(params),
            "inputs": _norm(inputs),
            "mock": bool(is_mock),
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
