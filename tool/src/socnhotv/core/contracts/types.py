from __future__ import annotations

import enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class PortType(str, enum.Enum):
    """Cổng kết nối chuẩn trong Node Canvas."""
    TEXT = "text"
    IMAGE = "image"
    IMAGE_LIST = "image[]"
    VIDEO = "video"
    AUDIO = "audio"
    SCRIPT = "script"
    SCENES = "scenes"
    CHARACTER = "character"
    CAPTIONS = "captions"
    COMPOSITION = "composition"


def is_port_compatible(source_type: PortType, target_type: PortType) -> bool:
    """Kiểm tra tính tương thích giữa 2 cổng kết nối.
    Hỗ trợ quy tắc chuyển đổi rõ ràng (ví dụ: IMAGE -> IMAGE_LIST).
    """
    if source_type == target_type:
        return True
    if source_type == PortType.IMAGE and target_type == PortType.IMAGE_LIST:
        return True
    return False


class ArtifactKind(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    CAPTIONS = "captions"
    COMPOSITION = "composition"


class ArtifactMeta(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    fps: Optional[float] = None
    aspect: Optional[str] = None  # e.g. "9:16", "16:9", "1:1", "4:5"


class ArtifactProvenance(BaseModel):
    node_id: str = Field(..., alias="nodeId")
    run_id: Optional[str] = Field(None, alias="runId")
    provider: str
    model: str
    params: Dict[str, Any] = Field(default_factory=dict)
    input_hashes: List[str] = Field(default_factory=list, alias="inputHashes")
    cost_usd: float = Field(0.0, alias="costUsd")
    created_at: str = Field(..., alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class Artifact(BaseModel):
    """Artifact bất biến (immutable), đại diện cho mọi sản phẩm sinh ra."""
    id: str
    kind: ArtifactKind
    uri: str  # Đường dẫn tương đối trong thư mục dự án (ví dụ: assets/abc1234.png)
    mime: str
    size: int
    hash: str
    meta: ArtifactMeta = Field(default_factory=ArtifactMeta)
    provenance: ArtifactProvenance

    model_config = ConfigDict(populate_by_name=True)


class Generation(BaseModel):
    """Lưu trữ một lần sinh kết quả của node.
    Người dùng có thể tạo lại (regenerate) nhiều lần mà không bị ghi đè,
    và ghim một generation làm kết quả chính của node.
    """
    id: str
    node_id: str = Field(..., alias="nodeId")
    params: Dict[str, Any] = Field(default_factory=dict)
    artifact_id: str = Field(..., alias="artifactId")
    cost_usd: float = Field(0.0, alias="costUsd")
    created_at: str = Field(..., alias="createdAt")
    is_pinned: bool = Field(False, alias="isPinned")

    model_config = ConfigDict(populate_by_name=True)


class NodeState(str, enum.Enum):
    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CACHED = "cached"


class PortDefinition(BaseModel):
    name: str
    port_type: PortType = Field(..., alias="portType")
    description: str = ""
    required: bool = True

    model_config = ConfigDict(populate_by_name=True)


class NodeDefinition(BaseModel):
    """Khai báo định nghĩa của một loại Node trong catalog."""
    type_name: str = Field(..., alias="typeName")
    display_name: str = Field(..., alias="displayName")
    category: str
    description: str
    input_ports: List[PortDefinition] = Field(default_factory=list, alias="inputPorts")
    output_ports: List[PortDefinition] = Field(default_factory=list, alias="outputPorts")
    default_params: Dict[str, Any] = Field(default_factory=dict, alias="defaultParams")
    mockable: bool = True

    model_config = ConfigDict(populate_by_name=True)


class NodePortInputRef(BaseModel):
    node_id: str = Field(..., alias="nodeId")
    output_port: str = Field(..., alias="outputPort")

    model_config = ConfigDict(populate_by_name=True)


class NodeInstance(BaseModel):
    """Một thực thể Node trên canvas đồ thị."""
    id: str
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    inputs: Dict[str, Union[NodePortInputRef, Any]] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    ui: Dict[str, Any] = Field(default_factory=dict)
    state: NodeState = NodeState.IDLE
    is_stale: bool = Field(False, alias="isStale")
    pinned_generation_id: Optional[str] = Field(None, alias="pinnedGenerationId")
    generations: List[Generation] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class Edge(BaseModel):
    """Dây nối truyền dữ liệu giữa các node."""
    id: str
    source_node_id: str = Field(..., alias="sourceNodeId")
    source_port: str = Field(..., alias="sourcePort")
    target_node_id: str = Field(..., alias="targetNodeId")
    target_port: str = Field(..., alias="targetPort")

    model_config = ConfigDict(populate_by_name=True)


class Graph(BaseModel):
    """Đồ thị node hoàn chỉnh của một dự án."""
    id: str
    project_id: str = Field(..., alias="projectId")
    name: str = "Default Graph"
    nodes: List[NodeInstance] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    updated_at: str = Field(..., alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class SSEEventType(str, enum.Enum):
    NODE_STATE = "node_state"
    NODE_PROGRESS = "node_progress"
    NODE_LOG = "node_log"
    COST_UPDATE = "cost_update"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class SSEEvent(BaseModel):
    """Sự kiện gửi qua Server-Sent Events cho giao diện."""
    event_type: SSEEventType = Field(..., alias="eventType")
    run_id: str = Field(..., alias="runId")
    node_id: Optional[str] = Field(None, alias="nodeId")
    state: Optional[NodeState] = None
    progress: Optional[float] = None
    message: Optional[str] = None
    cost_usd: Optional[float] = Field(None, alias="costUsd")
    timestamp: str

    model_config = ConfigDict(populate_by_name=True)
