"""Tests for Luồng H5: LipSync & Voice-Mouth Alignment."""
from __future__ import annotations

import subprocess
from pathlib import Path
import pytest

from socnhotv.video.lipsync.models import (
    AlignmentMode,
    CharacterType,
    FeasibilityStatus,
    HardwareRequirement,
    LipSyncMethod,
    LipSyncPlan,
    LipSyncResult,
)
from socnhotv.video.lipsync.evaluator import (
    LIPSYNC_REGISTRY,
    LipSyncEvaluator,
)
from socnhotv.video.lipsync.narrative_aligner import (
    NarrativeAligner,
    FFMPEG_EXE,
)
from socnhotv.video.lipsync.api_adapter import CloudLipSyncAdapter


def test_models_and_enums():
    """Kiểm tra tính toàn vẹn của các enum và data classes."""
    assert LipSyncMethod.MUTE_AND_VOICEOVER == "mute_and_voiceover"
    assert LipSyncMethod.LOCAL_OSS == "local_oss"
    assert LipSyncMethod.CLOUD_API == "cloud_api"
    assert LipSyncMethod.NATIVE_MODEL_TTS == "native_model_tts"

    assert CharacterType.ANTHROPOMORPHIC_3D == "anthropomorphic_3d"
    assert CharacterType.HUMAN_REALISTIC == "human_realistic"

    assert FeasibilityStatus.FEASIBLE_RECOMMENDED == "feasible_recommended"
    assert FeasibilityStatus.INFEASIBLE == "infeasible"


def test_evaluator_registry():
    """Kiểm tra sổ đăng ký tri thức tất cả các công cụ lip-sync."""
    tools = LipSyncEvaluator.list_all_evaluations()
    assert len(tools) >= 10, "Phải khảo sát tối thiểu 10 công cụ/model."

    tool_ids = {t.tool_id for t in tools}
    # (a)
    assert "narrative_aligner" in tool_ids
    # (b1) local oss
    assert "wav2lip" in tool_ids
    assert "sadtalker" in tool_ids
    assert "musetalk" in tool_ids
    assert "latentsync" in tool_ids
    assert "liveportrait" in tool_ids
    # (b2) cloud api
    assert "synclabs" in tool_ids
    assert "heygen_lipsync" in tool_ids
    assert "hedra" in tool_ids
    # (c) native model
    assert "native_veo_tts" in tool_ids
    assert "native_kling_lipsync" in tool_ids

    # Kiểm tra mỗi tool đều có official_url và terms_summary
    for t in tools:
        assert t.official_url.startswith("http"), f"{t.tool_id} thiếu link chính thức hợp lệ."
        assert len(t.terms_summary) > 5, f"{t.tool_id} thiếu tóm tắt điều khoản."
        assert CharacterType.ANTHROPOMORPHIC_3D in t.character_compatibility


def test_evaluator_recommendations():
    """Kiểm tra logic đề xuất kế hoạch xử lý theo các ràng buộc."""
    # Mặc định theo luật cứng: $0, không upload ảnh, nhân vật Sóc Bi (3D)
    plan_default = LipSyncEvaluator.recommend_plan(
        shot_id="S01",
        character_type=CharacterType.ANTHROPOMORPHIC_3D,
        audio_duration_sec=4.0,
        video_duration_sec=8.0,
        allow_paid=False,
        allow_external_upload=False,
    )
    assert plan_default.method == LipSyncMethod.MUTE_AND_VOICEOVER
    assert plan_default.tool_id == "narrative_aligner"
    assert plan_default.estimated_cost_usd == 0.0
    assert plan_default.requires_user_confirmation is False
    assert plan_default.requires_external_upload is False

    # Khi người dùng duyệt trả phí và cho phép upload ảnh ra ngoài
    plan_paid = LipSyncEvaluator.recommend_plan(
        shot_id="S01",
        character_type=CharacterType.ANTHROPOMORPHIC_3D,
        audio_duration_sec=4.0,
        video_duration_sec=8.0,
        allow_paid=True,
        allow_external_upload=True,
    )
    assert plan_paid.method == LipSyncMethod.CLOUD_API
    assert plan_paid.tool_id == "synclabs"
    assert plan_paid.estimated_cost_usd > 0.0
    assert plan_paid.requires_user_confirmation is True
    assert plan_paid.requires_external_upload is True


def test_narrative_aligner_file_not_found(tmp_path):
    """Kiểm tra xử lý lỗi khi file đầu vào không tồn tại."""
    aligner = NarrativeAligner()
    res = aligner.align_shot(
        shot_id="S01",
        video_path=tmp_path / "non_existent.mp4",
        audio_path=tmp_path / "non_existent.mp3",
        output_path=tmp_path / "out.mp4",
    )
    assert res.success is False
    assert "không tồn tại" in res.error_message


def test_narrative_aligner_execution_tmp(tmp_path):
    """Tạo video và audio mẫu trong tmp_path và chạy thật NarrativeAligner."""
    fake_video = tmp_path / "test_in.mp4"
    fake_audio = tmp_path / "test_in.mp3"
    fake_out = tmp_path / "test_out.mp4"

    # Tạo 1 video 2 giây màu cam bằng ffmpeg
    cmd_vid = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi",
        "-i", "color=c=orange:s=320x240:d=2.0",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=2.0",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        str(fake_video),
    ]
    subprocess.run(cmd_vid, capture_output=True, check=True)

    # Tạo 1 file mp3 thoại 1.5 giây
    cmd_aud = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=880:duration=1.5",
        "-c:a", "libmp3lame",
        str(fake_audio),
    ]
    subprocess.run(cmd_aud, capture_output=True, check=True)

    aligner = NarrativeAligner()

    # Test mode STRIP_ORIGINAL
    res = aligner.align_shot(
        shot_id="test_shot",
        video_path=fake_video,
        audio_path=fake_audio,
        output_path=fake_out,
        mode=AlignmentMode.STRIP_ORIGINAL,
        audio_start_offset_sec=0.2,
    )
    assert res.success is True
    assert fake_out.exists()
    assert res.metadata["video_duration"] >= 1.9
    assert res.execution_time_sec < 5.0  # Phải hoàn thành cực nhanh


def test_cloud_api_adapter_security_guards(tmp_path):
    """Kiểm tra SpendGuard và VaultGuard của CloudLipSyncAdapter."""
    adapter = CloudLipSyncAdapter(provider="synclabs", mock_mode=False)

    fake_video = tmp_path / "fake.mp4"
    fake_audio = tmp_path / "fake.mp3"
    fake_video.touch()
    fake_audio.touch()

    # 1. Chặn vì chưa cho phép upload ảnh
    res1 = adapter.process_shot(
        shot_id="S01",
        video_path=fake_video,
        audio_path=fake_audio,
        output_path=tmp_path / "out.mp4",
        confirm_upload=False,
        confirm_paid=True,
    )
    assert res1.success is False
    assert "BỊ CHẶN: Luật cứng cấm tải ảnh/video" in res1.error_message

    # 2. Chặn vì chưa phê duyệt chi phí tiền thật
    res2 = adapter.process_shot(
        shot_id="S01",
        video_path=fake_video,
        audio_path=fake_audio,
        output_path=tmp_path / "out.mp4",
        confirm_upload=True,
        confirm_paid=False,
    )
    assert res2.success is False
    assert "BỊ CHẶN: Chi phí ước tính" in res2.error_message

    # 3. Chế độ Mock luôn an toàn và trả về dự toán chi phí
    adapter_mock = CloudLipSyncAdapter(provider="synclabs", mock_mode=True)
    res_mock = adapter_mock.process_shot(
        shot_id="S01",
        video_path=fake_video,
        audio_path=fake_audio,
        output_path=tmp_path / "out.mp4",
        video_duration_sec=8.0,
    )
    assert res_mock.success is True
    assert res_mock.metadata["mock"] is True
    assert res_mock.cost_usd == 0.40  # 8s * 0.05 $/s
