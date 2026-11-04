from __future__ import annotations

from typing import Any
from socnhotv.core.contracts.types import NodeDefinition, PortDefinition, PortType


def register(registry: Any) -> None:
    """Register sources & intelligence nodes into NodeRegistry."""
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

    # 3. Phân tích Blueprint
    registry.register(
        NodeDefinition(
            type_name="blueprint_analyze",
            display_name="Phân tích Blueprint Video",
            category="Intelligence",
            description="Bóc tách cấu trúc video mẫu thành các nhịp Hook, Problem, Demo, Proof, Offer, CTA",
            input_ports=[
                PortDefinition(name="video", port_type=PortType.VIDEO, description="Video mẫu"),
            ],
            output_ports=[
                PortDefinition(name="blueprint", port_type=PortType.TEXT, description="Dữ liệu VideoBlueprint JSON"),
            ],
            default_params={},
            mockable=True,
        )
    )

    # 4. Kịch bản từ Blueprint (Affiliate/KOC)
    registry.register(
        NodeDefinition(
            type_name="script_from_blueprint",
            display_name="Sinh kịch bản KOC/Affiliate",
            category="Intelligence",
            description="Áp dụng cấu trúc Blueprint cho sản phẩm và nhân vật, kiểm tra tuân thủ chính sách quảng cáo",
            input_ports=[
                PortDefinition(name="blueprint", port_type=PortType.TEXT, description="Dữ liệu Blueprint mẫu"),
                PortDefinition(name="character", port_type=PortType.CHARACTER, description="Nhân vật KOC", required=False),
            ],
            output_ports=[
                PortDefinition(name="script", port_type=PortType.SCRIPT, description="Kịch bản phân cảnh hoàn chỉnh"),
                PortDefinition(name="render_request", port_type=PortType.TEXT, description="Cấu hình RenderRequest"),
            ],
            default_params={"generator_type": "koc_review", "voice_id": "soc-nho"},
            mockable=True,
        ),
        NodeDefinition(
            type_name="channel_insight",
            display_name="Phân tích Kênh Đối thủ",
            category="Intelligence",
            description="Bóc tách thống kê, chủ đề pillars, mẫu tiêu đề và công thức viral từ kênh YouTube/TikTok",
            input_ports=[
                PortDefinition(name="channel_url", port_type=PortType.TEXT, description="URL kênh đối thủ"),
            ],
            output_ports=[
                PortDefinition(name="blueprint", port_type=PortType.TEXT, description="Dữ liệu ChannelBlueprint"),
                PortDefinition(name="pillars", port_type=PortType.TEXT, description="Danh sách pillars nội dung"),
                PortDefinition(name="summary", port_type=PortType.TEXT, description="Tóm tắt phân tích kênh"),
            ],
            default_params={"max_videos": 50},
            mockable=True,
        )
    )
