"""Evaluator module for LipSync feasibility, hardware compatibility, and cost analysis (Luồng H5)."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from socnhotv.video.lipsync.models import (
    AlignmentMode,
    CharacterType,
    FeasibilityStatus,
    HardwareRequirement,
    LipSyncMethod,
    LipSyncPlan,
    ToolEvaluation,
)

logger = logging.getLogger("socnhotv.video.lipsync.evaluator")

# Sổ đăng ký tri thức tất cả các công cụ và phương pháp khảo sát
LIPSYNC_REGISTRY: Dict[str, ToolEvaluation] = {
    # (a) Tắt âm thanh gốc & Đồng bộ dẫn chuyện / Thoại OmniVoice
    "narrative_aligner": ToolEvaluation(
        tool_id="narrative_aligner",
        name="Narrator / Voiceover Alignment (Tắt tiếng gốc, đồng bộ thoại)",
        category=LipSyncMethod.MUTE_AND_VOICEOVER,
        official_url="https://github.com/vmaxmartis09/socnhotv",
        pricing_type="$0 Hoàn toàn miễn phí",
        cost_per_minute_usd=0.0,
        hardware=HardwareRequirement.CPU_OR_MPS,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.STYLIZED_2D: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.ABSTRACT: FeasibilityStatus.FEASIBLE_RECOMMENDED,
        },
        terms_summary="Mã nguồn mở nội bộ dự án, không ràng buộc thương mại, dữ liệu hoàn toàn offline.",
        requires_external_upload=False,
        notes="Giải pháp chuẩn mực cho phim hoạt hình thiếu nhi: Nhân vật diễn xuất hành động cơ thể, giọng OmniVoice đọc thoại dẫn chuyện mượt mà.",
    ),

    # (b1) Công cụ mã nguồn mở chạy máy cục bộ
    "wav2lip": ToolEvaluation(
        tool_id="wav2lip",
        name="Wav2Lip / Wav2Lip-GAN",
        category=LipSyncMethod.LOCAL_OSS,
        official_url="https://github.com/Rudrabha/Wav2Lip",
        pricing_type="$0 Open-Source (Trọng số nghiên cứu phi thương mại)",
        cost_per_minute_usd=0.0,
        hardware=HardwareRequirement.CPU_OR_MPS,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.INFEASIBLE,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="Giấy phép phi thương mại (Non-commercial research only cho weights gốc).",
        requires_external_upload=False,
        notes="Detector S3FD fail hoàn toàn trên mõm sóc/dê 3D (ValueError: Face not detected). Vùng miệng crop 96x96 mờ căm.",
    ),
    "sadtalker": ToolEvaluation(
        tool_id="sadtalker",
        name="SadTalker (CVPR 2023)",
        category=LipSyncMethod.LOCAL_OSS,
        official_url="https://github.com/OpenTalker/SadTalker",
        pricing_type="$0 Open-Source (CC-BY-NC 4.0)",
        cost_per_minute_usd=0.0,
        hardware=HardwareRequirement.CPU_OR_MPS,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.INFEASIBLE,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="CC-BY-NC 4.0 (Phi thương mại).",
        requires_external_upload=False,
        notes="Sử dụng 3DMM chuẩn mặt người. Không thể ánh xạ mô hình 3DMM lên khuôn mặt có mõm thú nhô ra và hai răng cửa lớn của Sóc Bi.",
    ),
    "musetalk": ToolEvaluation(
        tool_id="musetalk",
        name="MuseTalk 1.5 (Tencent TME Lyra Lab)",
        category=LipSyncMethod.LOCAL_OSS,
        official_url="https://github.com/TMElyralab/MuseTalk",
        pricing_type="$0 Open-Source (MIT / Apache 2.0)",
        cost_per_minute_usd=0.0,
        hardware=HardwareRequirement.NVIDIA_CUDA_8GB,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="MIT / Apache 2.0 (Thương mại OK).",
        requires_external_upload=False,
        notes="Yêu cầu bắt buộc NVIDIA GPU có CUDA. Không hỗ trợ macOS MPS native. VAE inpainting 256x256 tối ưu cho người thật.",
    ),
    "latentsync": ToolEvaluation(
        tool_id="latentsync",
        name="LatentSync (ByteDance late 2024)",
        category=LipSyncMethod.LOCAL_OSS,
        official_url="https://github.com/bytedance/LatentSync",
        pricing_type="$0 Open-Source (Research / CC-BY-NC)",
        cost_per_minute_usd=0.0,
        hardware=HardwareRequirement.NVIDIA_CUDA_24GB,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.STYLIZED_2D: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="Nghiên cứu mở, cần GPU dung lượng lớn.",
        requires_external_upload=False,
        notes="Chất lượng cao nhất trong các mã nguồn mở nhưng cực nặng (Stable Diffusion UNet + Whisper). Yêu cầu GPU NVIDIA ≥ 16GB VRAM, không chạy nổi trên Mac M4 16GB.",
    ),
    "liveportrait": ToolEvaluation(
        tool_id="liveportrait",
        name="LivePortrait (KwaiVGI animal mode)",
        category=LipSyncMethod.LOCAL_OSS,
        official_url="https://github.com/KwaiVGI/LivePortrait",
        pricing_type="$0 Open-Source (Apache 2.0 / Non-commercial for weights)",
        cost_per_minute_usd=0.0,
        hardware=HardwareRequirement.NVIDIA_CUDA_8GB,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_RECOMMENDED,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="Bản quyền trọng số nghiên cứu của Kuaishou.",
        requires_external_upload=False,
        notes="Hỗ trợ thú cưng (chó/mèo) nhưng CHỈ nhận video chuyển động dẫn động (driving video), KHÔNG nhận file âm thanh để sinh khẩu hình.",
    ),

    # (b2) Công cụ đám mây / API thương mại
    "synclabs": ToolEvaluation(
        tool_id="synclabs",
        name="Sync Labs Lipsync 2.0 / Sync-3 (sync.so)",
        category=LipSyncMethod.CLOUD_API,
        official_url="https://sync.so",
        pricing_type="Prepaid / Subscription + Usage ($0.04 - $0.08 / s)",
        cost_per_minute_usd=3.0,
        hardware=HardwareRequirement.CLOUD_ONLY,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.STYLIZED_2D: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.ABSTRACT: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
        },
        terms_summary="Thương mại qua gói trả phí. Xử lý trên server đám mây của Sync Labs tại Mỹ.",
        requires_external_upload=True,
        notes="Hỗ trợ tốt nhân vật 3D hoạt hình zero-shot, nhưng tốn chi phí (~$3.00/phút video) và bắt buộc tải video lên máy chủ bên thứ ba.",
    ),
    "heygen_lipsync": ToolEvaluation(
        tool_id="heygen_lipsync",
        name="HeyGen LipSync API (POST /v3/lipsyncs)",
        category=LipSyncMethod.CLOUD_API,
        official_url="https://docs.heygen.com",
        pricing_type="Prepaid API Wallet ($0.014 - $0.029 / s)",
        cost_per_minute_usd=1.2,
        hardware=HardwareRequirement.CLOUD_ONLY,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="Prepaid credits có hạn 12 tháng. Phải tuân thủ HeyGen Acceptable Use Policy.",
        requires_external_upload=True,
        notes="Tối ưu cho người thật và avatar người. Thử nghiệm trên thú 3D hoạt hình mõm dài thường xuyên bị méo hoặc từ chối.",
    ),
    "did_lipsync": ToolEvaluation(
        tool_id="did_lipsync",
        name="D-ID Video Translate & LipSync API",
        category=LipSyncMethod.CLOUD_API,
        official_url="https://www.d-id.com",
        pricing_type="Gói Build $18/tháng (~$1.12 / phút, tính block 15s)",
        cost_per_minute_usd=1.12,
        hardware=HardwareRequirement.CLOUD_ONLY,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.INFEASIBLE,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="D-ID ToS. Bản trial có watermark toàn màn hình.",
        requires_external_upload=True,
        notes="Face detection giới hạn cho mặt người, không nhận diện được thú 3D hoạt hình.",
    ),
    "hedra": ToolEvaluation(
        tool_id="hedra",
        name="Hedra Character-1 / Character-2 API",
        category=LipSyncMethod.CLOUD_API,
        official_url="https://www.hedra.com",
        pricing_type="Pay-as-you-go ($0.025 / s, ~$1.50 / phút)",
        cost_per_minute_usd=1.5,
        hardware=HardwareRequirement.CLOUD_ONLY,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.STYLIZED_2D: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.ABSTRACT: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
        },
        terms_summary="Dịch vụ đám mây trả trước, tính theo giây output.",
        requires_external_upload=True,
        notes="Tạo video nói từ 1 ảnh + 1 file audio. Hỗ trợ nhân vật 3D hoạt hình tốt, nhưng chỉ sinh cận cảnh đầu/nửa người tĩnh, không có chuyển động cảnh quay linh hoạt.",
    ),

    # (c) Sinh clip có thoại đúng lời ngay từ model
    "native_veo_tts": ToolEvaluation(
        tool_id="native_veo_tts",
        name="Google Veo 3.1 Native Audio Generation",
        category=LipSyncMethod.NATIVE_MODEL_TTS,
        official_url="https://deepmind.google/technologies/veo/",
        pricing_type="Trả phí qua Google Cloud / Vertex AI",
        cost_per_minute_usd=6.0,
        hardware=HardwareRequirement.CLOUD_ONLY,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.INFEASIBLE,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="Google Cloud Terms of Service.",
        requires_external_upload=False,
        notes="Veo tự sinh tiếng theo prompt tiếng Anh, KHÔNG nhận audio đầu vào từ OmniVoice và KHÔNG phát âm chuẩn tiếng Việt có dấu. Vi phạm luật DNA âm thanh của dự án.",
    ),
    "native_kling_lipsync": ToolEvaluation(
        tool_id="native_kling_lipsync",
        name="Kling AI LipSync (Web Studio Tool)",
        category=LipSyncMethod.NATIVE_MODEL_TTS,
        official_url="https://klingai.com",
        pricing_type="Credit hằng ngày (66 free/ngày) hoặc Trả phí",
        cost_per_minute_usd=1.2,
        hardware=HardwareRequirement.CLOUD_ONLY,
        character_compatibility={
            CharacterType.ANTHROPOMORPHIC_3D: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.HUMAN_REALISTIC: FeasibilityStatus.FEASIBLE_PAID_API,
            CharacterType.STYLIZED_2D: FeasibilityStatus.EXPERIMENTAL_GLITCHY,
            CharacterType.ABSTRACT: FeasibilityStatus.INFEASIBLE,
        },
        terms_summary="Kling AI Terms of Service.",
        requires_external_upload=True,
        notes="Hỗ trợ nạp audio + ảnh/video trên Web Studio. Người dùng có thể làm tay, nhưng chưa có API headless tự động và đòi hỏi upload ảnh lên server Trung Quốc.",
    ),
}


class LipSyncEvaluator:
    """Bộ đánh giá tính khả thi và lập kế hoạch xử lý khẩu hình."""

    @staticmethod
    def get_evaluation(tool_id: str) -> Optional[ToolEvaluation]:
        return LIPSYNC_REGISTRY.get(tool_id)

    @staticmethod
    def list_all_evaluations() -> List[ToolEvaluation]:
        return list(LIPSYNC_REGISTRY.values())

    @staticmethod
    def recommend_plan(
        shot_id: str,
        character_type: CharacterType = CharacterType.ANTHROPOMORPHIC_3D,
        audio_duration_sec: float = 4.0,
        video_duration_sec: float = 8.0,
        allow_paid: bool = False,
        allow_external_upload: bool = False,
    ) -> LipSyncPlan:
        """Đưa ra kế hoạch tối ưu nhất tuân thủ mọi luật cứng của dự án.
        
        Quy tắc ưu tiên:
        1. Tuân thủ luật cứng: $0 tiền thật (trừ khi allow_paid=True) và không upload ảnh ngoài (trừ khi allow_external_upload=True).
        2. Với nhân vật Anthropomorphic 3D (Sóc Bi, Dê Mun): Các tool mã nguồn mở hiện tại (Wav2Lip, SadTalker, MuseTalk)
           hoặc fail face detection hoặc thiếu phần cứng NVIDIA GPU.
        3. Do đó, phương án khả thi 100% duy nhất trên Mac M4 $0 là Lựa chọn (a) Narrative / Voiceover Alignment.
        """
        reasons: List[str] = []

        # Nếu người dùng cấp phép trả phí VÀ cho phép upload ảnh ra ngoài:
        if allow_paid and allow_external_upload:
            cost = (video_duration_sec / 60.0) * LIPSYNC_REGISTRY["synclabs"].cost_per_minute_usd
            return LipSyncPlan(
                shot_id=shot_id,
                method=LipSyncMethod.CLOUD_API,
                tool_id="synclabs",
                estimated_cost_usd=round(cost, 3),
                estimated_time_sec=15.0,
                requires_user_confirmation=True,
                requires_external_upload=True,
                reasons=[
                    "Người dùng đã cho phép trả phí và tải ảnh lên server ngoài.",
                    "SyncLabs Sync-3 hỗ trợ tốt khuôn mặt 3D hoạt hình.",
                ],
            )

        # Mặc định theo luật cứng:
        reasons.append("Chính sách $0 và bảo vệ ảnh nhân vật: Không gọi API trả phí, không upload ảnh lên host ngoài.")
        reasons.append(f"Nhân vật '{character_type.value}': Wav2Lip/SadTalker thất bại trên mõm thú; MuseTalk/LatentSync đòi hỏi GPU NVIDIA CUDA.")
        reasons.append("Lựa chọn (a) Narrative Alignment chạy 100% offline trên Mac M4, tốc độ siêu tốc (>200x realtime), $0, không méo mặt.")

        return LipSyncPlan(
            shot_id=shot_id,
            method=LipSyncMethod.MUTE_AND_VOICEOVER,
            tool_id="narrative_aligner",
            estimated_cost_usd=0.0,
            estimated_time_sec=0.2,
            requires_user_confirmation=False,
            requires_external_upload=False,
            reasons=reasons,
        )
