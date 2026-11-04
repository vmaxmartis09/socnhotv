from __future__ import annotations

from typing import Any
from socnhotv.core.contracts.types import NodeDefinition, PortDefinition, PortType


def register(registry: Any) -> None:
    """Register sources nodes into NodeRegistry."""
    # 1. Nguồn Video
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

    # 2. Bản địa hoá Douyin / TikTok (Localize)
    registry.register(
        NodeDefinition(
            type_name="localize",
            display_name="Bản địa hoá (Douyin/TikTok -> VI)",
            category="Intelligence",
            description="Tự động nhận diện lời thoại (ASR), dịch câu, viết lại theo giọng thương hiệu và lồng tiếng",
            input_ports=[
                PortDefinition(name="video", port_type=PortType.VIDEO, description="Video nguồn"),
                PortDefinition(name="audio", port_type=PortType.AUDIO, description="Audio gốc của video"),
            ],
            output_ports=[
                PortDefinition(name="script", port_type=PortType.SCRIPT, description="Kịch bản tiếng Việt đã viết lại"),
                PortDefinition(name="audio", port_type=PortType.AUDIO, description="Giọng đọc tiếng Việt (-14 LUFS)"),
                PortDefinition(name="captions", port_type=PortType.CAPTIONS, description="Phụ đề tiếng Việt"),
            ],
            default_params={
                "mode": "R",
                "style": "faithful",
                "voice_id": "soc-nho",
                "auto_draft": True,
            },
            mockable=True,
        )
    )
