from __future__ import annotations

from typing import Dict, List, Optional
from socnhotv.core.contracts.types import NodeDefinition, PortDefinition, PortType


class NodeRegistry:
    """Đăng ký và quản lý danh mục định nghĩa các loại Node (Node Definitions)."""

    _definitions: Dict[str, NodeDefinition] = {}

    @classmethod
    def register(cls, definition: NodeDefinition) -> None:
        cls._definitions[definition.type_name] = definition

    @classmethod
    def get(cls, type_name: str) -> Optional[NodeDefinition]:
        return cls._definitions.get(type_name)

    @classmethod
    def list_all(cls) -> List[NodeDefinition]:
        return list(cls._definitions.values())

    @classmethod
    def effective_ports(cls, node_type: str, params: Optional[dict]) -> tuple[list, list]:
        """Cổng hiệu lực của một node: ưu tiên ghi đè riêng trong params['_ports'] (nếu có)."""
        base = cls.get(node_type)
        base_in = list(base.input_ports) if base else []
        base_out = list(base.output_ports) if base else []
        override = (params or {}).get("_ports")
        if not isinstance(override, dict):
            return base_in, base_out
        try:
            ins = [PortDefinition.model_validate(p) for p in override.get("inputs", [])] if "inputs" in override else base_in
            outs = [PortDefinition.model_validate(p) for p in override.get("outputs", [])] if "outputs" in override else base_out
        except Exception:
            return base_in, base_out
        return ins, outs

    @classmethod
    def initialize_defaults(cls) -> None:
        """Đăng ký toàn bộ 13 Node chuẩn theo bảng hợp đồng dữ liệu."""
        cls._definitions.clear()

        # 1. Văn bản
        cls.register(
            NodeDefinition(
                type_name="text",
                display_name="Văn bản / Prompt",
                category="Input",
                description="Nhập văn bản tự do, ý tưởng hoặc prompt tùy chỉnh",
                input_ports=[],
                output_ports=[
                    PortDefinition(name="text", port_type=PortType.TEXT, description="Văn bản đầu ra")
                ],
                default_params={"content": ""},
                mockable=True,
            )
        )

        # 2. Ảnh
        cls.register(
            NodeDefinition(
                type_name="image",
                display_name="Tải ảnh / Thư viện",
                category="Input",
                description="Tải ảnh lên hoặc chọn ảnh từ thư viện tài nguyên",
                input_ports=[],
                output_ports=[
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh đã chọn")
                ],
                default_params={"uri": ""},
                mockable=True,
            )
        )

        # 3. Nhân vật
        cls.register(
            NodeDefinition(
                type_name="character",
                display_name="Nhân vật (Character Bible)",
                category="Identity",
                description="Chọn nhân vật của dự án (DNA ảnh tham chiếu, prompt lock, voiceId, bộ nhớ)",
                input_ports=[],
                output_ports=[
                    PortDefinition(name="character", port_type=PortType.CHARACTER, description="Dữ liệu hồ sơ nhân vật"),
                    PortDefinition(name="reference_images", port_type=PortType.IMAGE_LIST, description="Danh sách ảnh tham chiếu DNA"),
                ],
                default_params={"characterId": "soc_nho"},
                mockable=True,
            )
        )

        # 4. Kịch bản
        cls.register(
            NodeDefinition(
                type_name="script",
                display_name="Kịch bản phân cảnh",
                category="Structure",
                description="Biến kịch bản thành danh sách cảnh có prompt ảnh, chuyển động và lời thoại",
                input_ports=[
                    PortDefinition(name="text", port_type=PortType.TEXT, description="Ý tưởng hoặc cốt truyện", required=False)
                ],
                output_ports=[
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Danh sách phân cảnh cấu trúc"),
                    PortDefinition(name="prompt", port_type=PortType.TEXT, description="Prompt tạo ảnh/video theo cảnh"),
                    PortDefinition(name="dialogue", port_type=PortType.TEXT, description="Lời thoại theo cảnh"),
                ],
                default_params={"mode": "ai", "rawScript": "", "targetSceneCount": 6, "targetDurationSec": 45},
                mockable=True,
            )
        )

        # 5. Phân tích (Vision Analyze)
        cls.register(
            NodeDefinition(
                type_name="vision_analyze",
                display_name="Phân tích Video / Ảnh",
                category="Intelligence",
                description="Phân tích cấu trúc video, góc quay, nhịp cảnh và lời thoại qua model nhìn",
                input_ports=[
                    PortDefinition(name="video", port_type=PortType.VIDEO, description="Video nguồn để phân tích", required=False),
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh nguồn để phân tích", required=False),
                ],
                output_ports=[
                    PortDefinition(name="script", port_type=PortType.SCRIPT, description="Kịch bản cấu trúc trích xuất"),
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Danh sách phân cảnh trích xuất"),
                ],
                default_params={"goal": "extract_scenes_and_dialogue"},
                mockable=True,
            )
        )

        # 6. Kiểm tra (Quality Gate)
        cls.register(
            NodeDefinition(
                type_name="quality_check",
                display_name="Kiểm tra chất lượng (Gate)",
                category="Quality",
                description="Chấm điểm ảnh trước khi tốn tiền tạo video",
                input_ports=[
                    PortDefinition(name="media", port_type=PortType.IMAGE, description="Ảnh hoặc video cần thẩm định", required=False),
                    PortDefinition(name="criteria", port_type=PortType.TEXT, description="Tiêu chí thẩm định (ví dụ: đúng đuôi xù, áo vàng)", required=False),
                    PortDefinition(name="text", port_type=PortType.TEXT, description="Lời nói / kịch bản / prompt cần kiểm chính sách", required=False),
                    PortDefinition(name="captions", port_type=PortType.CAPTIONS, description="Caption cần kiểm chính sách", required=False),
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Danh sách cảnh (lời thoại + prompt) cần kiểm", required=False),
                    PortDefinition(name="policy", port_type=PortType.POLICY, description="Chính sách riêng (mặc định: chính sách của dự án)", required=False),
                ],
                output_ports=[
                    PortDefinition(name="media", port_type=PortType.IMAGE, description="Media đã qua kiểm duyệt"),
                    PortDefinition(name="pass_fail", port_type=PortType.TEXT, description="Kết quả đạt/không đạt + điểm + vi phạm chính sách"),
                    PortDefinition(name="violations", port_type=PortType.TEXT, description="Danh sách từ ngữ vi phạm chính sách", required=False),
                ],
                default_params={
                    "thresholdScore": 0.85,
                    "maxRetries": 2,
                    "policyAutoScan": True,
                    "criteria": "Nhân vật Sóc Nhỏ 100cm, áo phông vàng, quần short đen, đuôi xù lớn, không chữ lạ",
                },
                mockable=True,
            )
        )

        # 6b. Chính sách nội dung (xuyên suốt dự án)
        cls.register(
            NodeDefinition(
                type_name="policy",
                display_name="Chính sách nội dung",
                category="Quality",
                description="Chính sách của dự án (từ cấm, mức vi phạm) — nối vào node Kiểm tra chất lượng hoặc để mặc định theo dự án",
                input_ports=[],
                output_ports=[
                    PortDefinition(name="policy", port_type=PortType.POLICY, description="Chính sách nội dung đang áp dụng")
                ],
                default_params={"extraTerms": [], "extraSeverity": "block"},
                mockable=True,
            )
        )

        # 7. Tạo ảnh (Image Gen)
        cls.register(
            NodeDefinition(
                type_name="image_gen",
                display_name="Tạo ảnh AI",
                category="Generation",
                description="Tạo ảnh từ prompt mô tả kết hợp các ảnh tham chiếu nhận diện nhân vật",
                input_ports=[
                    PortDefinition(name="prompt", port_type=PortType.TEXT, description="Prompt mô tả cảnh", required=False),
                    PortDefinition(name="references", port_type=PortType.IMAGE_LIST, description="Ảnh tham chiếu DNA", required=False),
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh mẫu tham chiếu", required=False),
                    PortDefinition(
                        name="scenes",
                        port_type=PortType.SCENES,
                        description="Lặp theo cảnh: nối danh sách cảnh để tạo mỗi cảnh 1 ảnh",
                        required=False,
                    ),
                ],
                output_ports=[
                    PortDefinition(name="images", port_type=PortType.IMAGE_LIST, description="Danh sách ảnh sinh ra"),
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh đại diện / khung đầu tiên sinh ra"),
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Danh sách cảnh đã gắn ảnh (khi lặp theo cảnh)"),
                ],
                default_params={
                    "prompt": "",
                    "model": "mock-image",
                    "aspectRatio": "9:16",
                    "resolution": "1080p",
                    "referenceImages": [],
                    "n": 1,
                    "seed": None,
                },
                mockable=True,
            )
        )

        # 8. Sửa ảnh (Image Edit)
        cls.register(
            NodeDefinition(
                type_name="image_edit",
                display_name="Sửa ảnh / Tách trang phục",
                category="Generation",
                description="Chỉnh sửa chi tiết hoặc thay đổi trang phục trên ảnh gốc",
                input_ports=[
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh gốc cần sửa"),
                    PortDefinition(name="references", port_type=PortType.IMAGE_LIST, description="Ảnh tham chiếu mới", required=False),
                    PortDefinition(name="prompt", port_type=PortType.TEXT, description="Mô tả chỉnh sửa", required=False),
                ],
                output_ports=[
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh kết quả sau sửa")
                ],
                default_params={"model": "mock-image", "aspectRatio": "9:16"},
                mockable=True,
            )
        )

        # 9. Tạo video (Video Gen)
        cls.register(
            NodeDefinition(
                type_name="video_gen",
                display_name="Tạo video chuyển động",
                category="Generation",
                description="Biến ảnh khung đầu thành video chuyển động 3D qua model Veo / LTX",
                input_ports=[
                    PortDefinition(name="first_frame", port_type=PortType.IMAGE, description="Ảnh khung đầu (First frame)", required=False),
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh khung đầu (alias)", required=False),
                    PortDefinition(name="prompt", port_type=PortType.TEXT, description="Prompt chuyển động camera", required=False),
                    PortDefinition(name="references", port_type=PortType.IMAGE_LIST, description="Ảnh tham chiếu phụ", required=False),
                ],
                output_ports=[
                    PortDefinition(name="video", port_type=PortType.VIDEO, description="Clip video sinh ra")
                ],
                default_params={
                    "model": "mock-video",
                    "durationSec": 8,
                    "aspectRatio": "9:16",
                    "hasAudio": False,
                },
                mockable=True,
            )
        )

        # 10. Giọng đọc (Voice TTS)
        cls.register(
            NodeDefinition(
                type_name="voice_tts",
                display_name="Văn bản thành giọng nói",
                category="Audio",
                description="Đọc lời thoại kịch bản bằng giọng Sóc Nhỏ (soc-nho) chuẩn ngữ điệu cảm xúc",
                input_ports=[
                    PortDefinition(name="text", port_type=PortType.TEXT, description="Lời thoại cần đọc", required=False),
                    PortDefinition(name="character", port_type=PortType.CHARACTER, description="Hồ sơ nhân vật chứa voiceId", required=False),
                ],
                output_ports=[
                    PortDefinition(name="audio", port_type=PortType.AUDIO, description="Tệp âm thanh MP3 đã master -14 LUFS")
                ],
                default_params={
                    "text": "",
                    "voiceId": "soc-nho",
                    "tempo": 1.10,
                    "mastering": True,
                },
                mockable=True,
            )
        )

        # 11. Phụ đề (Captions)
        cls.register(
            NodeDefinition(
                type_name="captions",
                display_name="Phụ đề Karaoke (Whisper)",
                category="Audio",
                description="Trích xuất phụ đề từng từ khớp mốc thời gian (Word-level timestamps)",
                input_ports=[
                    PortDefinition(name="audio", port_type=PortType.AUDIO, description="Tệp âm thanh thoại"),
                    PortDefinition(name="text", port_type=PortType.TEXT, description="Text đối chiếu chuẩn", required=False),
                ],
                output_ports=[
                    PortDefinition(name="captions", port_type=PortType.CAPTIONS, description="Dữ liệu phụ đề mốc thời gian")
                ],
                default_params={"language": "vi", "style": "kinetic_karaoke"},
                mockable=True,
            )
        )

        # 12. Dựng (HyperFrames Render)
        cls.register(
            NodeDefinition(
                type_name="hyperframes_render",
                display_name="Dựng phim HyperFrames",
                category="Composition",
                description="Ghép các phân cảnh, chạy phụ đề karaoke, chèn BGM ducking chuẩn Safe Zone 9:16",
                input_ports=[
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Cấu trúc các cảnh", required=False),
                    PortDefinition(name="audio", port_type=PortType.AUDIO, description="Thoại chính voiceover", required=False),
                    PortDefinition(name="voice", port_type=PortType.AUDIO, description="Thoại chính voiceover (alias)", required=False),
                    PortDefinition(name="captions", port_type=PortType.CAPTIONS, description="Phụ đề karaoke", required=False),
                    PortDefinition(name="bgm", port_type=PortType.AUDIO, description="Nhạc nền BGM", required=False),
                    PortDefinition(name="video", port_type=PortType.VIDEO, description="Video clip đầu vào", required=False),
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh tĩnh đầu vào", required=False),
                ],
                output_ports=[
                    PortDefinition(name="video", port_type=PortType.VIDEO, description="Video thành phẩm MP4")
                ],
                default_params={
                    "aspectRatio": "9:16",
                    "template": "default_cartoon",
                    "templateId": "default_cartoon",
                    "platform": "tiktok",
                    "safeZonePaddingTop": 180,
                    "safeZonePaddingBottom": 320,
                    "duckingLevel": 0.25,
                },
                mockable=True,
            )
        )

        # 13. Xuất thành phẩm (Export)
        cls.register(
            NodeDefinition(
                type_name="export",
                display_name="Xuất & Phân phối",
                category="Output",
                description="Xuất video hoàn chỉnh vào thư mục output/ và tạo manifest đóng gói",
                input_ports=[
                    PortDefinition(name="video", port_type=PortType.VIDEO, description="Video cần xuất bản")
                ],
                output_ports=[
                    PortDefinition(name="manifest", port_type=PortType.COMPOSITION, description="Manifest thành phẩm")
                ],
                default_params={"platforms": ["tiktok", "youtube"], "outputFileName": "final_video.mp4"},
                mockable=True,
            )
        )

        # 14. Nhân vật từ ảnh (đơn giản: tải 1 ảnh làm nhân vật)
        cls.register(
            NodeDefinition(
                type_name="character_image",
                display_name="Nhân vật từ ảnh",
                category="Identity",
                description="Dùng một ảnh bất kỳ làm nhân vật tham chiếu, không cần tạo hồ sơ đầy đủ",
                input_ports=[],
                output_ports=[
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh nhân vật"),
                    PortDefinition(name="reference_images", port_type=PortType.IMAGE_LIST, description="Ảnh tham chiếu nhân vật"),
                ],
                default_params={"uri": "", "name": ""},
                mockable=True,
            )
        )

        # 15. Cảnh (ghép ảnh + lời thoại thành một cảnh)
        cls.register(
            NodeDefinition(
                type_name="scene",
                display_name="Cảnh",
                category="Structure",
                description="Ghép một ảnh và lời thoại thành một cảnh để dựng phim",
                input_ports=[
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh của cảnh"),
                    PortDefinition(name="text", port_type=PortType.TEXT, description="Lời thoại hoặc mô tả cảnh", required=False),
                ],
                output_ports=[
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Cảnh đã ghép"),
                    PortDefinition(name="image", port_type=PortType.IMAGE, description="Ảnh của cảnh"),
                ],
                default_params={"title": "Cảnh mới", "durationSec": 6},
                mockable=True,
            )
        )

        # 16. Chuyển cảnh
        cls.register(
            NodeDefinition(
                type_name="transition",
                display_name="Chuyển cảnh",
                category="Structure",
                description="Đặt kiểu chuyển cảnh (mờ dần, trượt, cắt) giữa các cảnh",
                input_ports=[
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Các cảnh cần chuyển tiếp"),
                ],
                output_ports=[
                    PortDefinition(name="scenes", port_type=PortType.SCENES, description="Các cảnh kèm chuyển cảnh"),
                ],
                default_params={"style": "fade", "durationSec": 0.5},
                mockable=True,
            )
        )

        from socnhotv.core.nodes.plugins import load_all
        load_all(cls)


# Khởi tạo ngay khi module được nạp
NodeRegistry.initialize_defaults()
