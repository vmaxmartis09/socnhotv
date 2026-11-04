from __future__ import annotations

from typing import Any
from socnhotv.core.contracts.types import NodeDefinition, PortDefinition, PortType


def register(registry: Any) -> None:
    """Register sources nodes into NodeRegistry."""
    registry.register(
        NodeDefinition(
            type_name="source_video",
            display_name="Nguồn Video (Douyin/YT/Local)",
            category="Input",
            description="Tải và trích xuất video, âm thanh, metadata từ liên kết mạng xã hội hoặc tập tin nguồn",
            input_ports=[
                PortDefinition(
                    name="url",
                    port_type=PortType.TEXT,
                    description="Đường dẫn video (Douyin, TikTok, YouTube) hoặc mã nguồn",
                    required=False,
                ),
            ],
            output_ports=[
                PortDefinition(name="video", port_type=PortType.VIDEO, description="Video nguồn đã tải"),
                PortDefinition(name="audio", port_type=PortType.AUDIO, description="Audio tách từ video (16k mono)"),
                PortDefinition(name="metadata", port_type=PortType.TEXT, description="Thông tin tiêu đề, mô tả, chỉ số tương tác"),
            ],
            default_params={"url": "", "rights": "reference_only"},
            mockable=True,
        )
    )
