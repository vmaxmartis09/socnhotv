from __future__ import annotations

from typing import Any
from socnhotv.core.contracts.types import NodeDefinition, PortDefinition, PortType


def register(registry: Any) -> None:
    """Đăng ký các Node video nâng cao vào NodeRegistry."""

    # 1. Template Render Node
    registry.register(
        NodeDefinition(
            type_name="template_render",
            display_name="Dựng video theo Template",
            category="Composition",
            description="Đổ dữ liệu slot vào HyperFrames Template và render chuẩn đa nền tảng",
            input_ports=[
                PortDefinition(name="text", port_type=PortType.TEXT, description="Văn bản / Hook đầu vào", required=False),
                PortDefinition(name="script", port_type=PortType.SCRIPT, description="Kịch bản phân cảnh", required=False),
                PortDefinition(name="images", port_type=PortType.IMAGE_LIST, description="Danh sách ảnh B-roll", required=False),
                PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh đơn sản phẩm", required=False),
                PortDefinition(name="video", port_type=PortType.VIDEO, description="Clip video nguồn", required=False),
                PortDefinition(name="audio", port_type=PortType.AUDIO, description="Thoại chính voiceover", required=False),
                PortDefinition(name="voice_clips", port_type=PortType.VOICE_CLIPS, description="Thoại từng câu từ chức năng Nói của nhân vật (tự ghép thành 1 giọng)", required=False),
                PortDefinition(name="reference_images", port_type=PortType.IMAGE_LIST, description="Ảnh nhân vật (làm avatar KOC)", required=False),
            ],
            output_ports=[
                PortDefinition(name="video", port_type=PortType.VIDEO, description="Video thành phẩm MP4")
            ],
            default_params={
                "template_id": "tiktok-sales-v1",
                "platforms": ["tiktok"],
                "slot_mapping": {},
            },
            mockable=True,
        )
    )

    # 2. Platform Export Node
    registry.register(
        NodeDefinition(
            type_name="platform_export",
            display_name="Xuất đa nền tảng (Fit Strategy)",
            category="Output",
            description="Tự động biến đổi kích thước video sang các tỷ lệ đa nền tảng (cover, contain, blur-pad)",
            input_ports=[
                PortDefinition(name="video", port_type=PortType.VIDEO, description="Video nguồn cần chuyển đổi", required=True)
            ],
            output_ports=[
                PortDefinition(name="video", port_type=PortType.VIDEO, description="Video thành phẩm theo tỷ lệ mới")
            ],
            default_params={
                "target_platforms": ["tiktok", "youtube", "facebook"],
                "fit_strategy": "cover",
            },
            mockable=True,
        )
    )
