from __future__ import annotations

import struct
import time
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.storage.project_store import ProjectStore


def create_minimal_png_bytes(width: int = 1080, height: int = 1920) -> bytes:
    """Tạo tệp PNG nhị phân hợp lệ 100% bằng Pillow cho Mock Image."""
    import io
    from PIL import Image

    # Tạo ảnh RGB màu tím primary (#6d4aff)
    img = Image.new("RGB", (width, height), color=(109, 74, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_minimal_mp4_bytes() -> bytes:
    """Tạo tệp MP4 dummy hợp lệ (ISO Media / MP4 v2)."""
    # ftyp box
    ftyp_data = b"isom\x00\x00\x02\x00isomiso2mp41"
    ftyp_box = struct.pack(">I", len(ftyp_data) + 8) + b"ftyp" + ftyp_data

    # mdat box
    mdat_data = b"MOCK_VIDEO_DATA_SOCNHOTV"
    mdat_box = struct.pack(">I", len(mdat_data) + 8) + b"mdat" + mdat_data

    return ftyp_box + mdat_box


def create_minimal_wav_bytes(duration_sec: float = 4.0) -> bytes:
    """Tạo tệp WAV PCM âm thanh hợp lệ cho Mock Voice."""
    sample_rate = 22050
    num_samples = int(sample_rate * duration_sec)
    data_size = num_samples * 2

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM
        1,  # mono
        sample_rate,
        sample_rate * 2,
        2,  # block align
        16,  # bits per sample
        b"data",
        data_size,
    )
    # Tắt tiếng (silence)
    pcm_data = b"\x00" * data_size
    return header + pcm_data


class MockProvider(BaseProvider):
    """Provider giả lập hoạt động của các Model AI (Gemini, Veo, OmniVoice) để kiểm thử."""

    def __init__(self, store: ProjectStore):
        self.store = store

    def provider_name(self) -> str:
        return "mock"

    async def generate_images(
        self,
        prompt: str,
        references: Optional[List[str]] = None,
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        n: int = 1,
        seed: Optional[int] = None,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> List[Artifact]:
        artifacts = []
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        # Ưu tiên lấy ảnh thật từ tập Sóc Nhỏ nếu tồn tại trong project_dir
        real_scene_img = (
            self.store.project_dir
            / "content"
            / "episodes"
            / "soc-nho-sau-rang"
            / "scenes"
            / "canh_01.jpg"
        )
        real_char_img = (
            self.store.project_dir / "characters" / "soc_nho" / "soc_nho_01.png"
        )
        if "master dna" in prompt.lower() and real_char_img.exists():
            img_bytes = real_char_img.read_bytes()
            ext = "png"
        elif real_scene_img.exists():
            img_bytes = real_scene_img.read_bytes()
            ext = "jpg"
        else:
            img_bytes = create_minimal_png_bytes(width=width, height=height)
            ext = "png"

        for i in range(max(1, n)):
            provenance = ArtifactProvenance(
                node_id=node_id,
                run_id=run_id,
                provider="mock",
                model="mock-image-v1",
                params={
                    "prompt": prompt,
                    "aspectRatio": aspect_ratio,
                    "resolution": resolution,
                    "index": i,
                    "seed": seed,
                },
                input_hashes=references or [],
                cost_usd=0.0,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            meta = ArtifactMeta(width=width, height=height, aspect=aspect_ratio)
            artifact = self.store.store_bytes(
                data=img_bytes,
                ext=ext,
                kind=ArtifactKind.IMAGE,
                provenance=provenance,
                meta=meta,
            )
            artifacts.append(artifact)

        return artifacts

    async def generate_video(
        self,
        prompt: str,
        first_frame_uri: Optional[str] = None,
        duration_sec: float = 8.0,
        aspect_ratio: str = "9:16",
        has_audio: bool = False,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        mp4_bytes = create_minimal_mp4_bytes()

        provenance = ArtifactProvenance(
            node_id=node_id,
            run_id=run_id,
            provider="mock",
            model="mock-veo-video-v1",
            params={
                "prompt": prompt,
                "firstFrameUri": first_frame_uri,
                "durationSec": duration_sec,
                "aspectRatio": aspect_ratio,
                "hasAudio": has_audio,
            },
            input_hashes=[first_frame_uri] if first_frame_uri else [],
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        meta = ArtifactMeta(
            width=width,
            height=height,
            duration=duration_sec,
            fps=24.0,
            aspect=aspect_ratio,
        )

        return self.store.store_bytes(
            data=mp4_bytes,
            ext="mp4",
            kind=ArtifactKind.VIDEO,
            provenance=provenance,
            meta=meta,
        )

    async def speak_voice(
        self,
        text: str,
        voice_id: str = "soc-nho",
        tempo: float = 1.10,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        # Tính thời lượng ước lượng theo số từ (trung bình 3 từ / giây)
        words_count = max(1, len(text.split()))
        est_duration = round(words_count / 3.0 / tempo, 2)
        wav_bytes = create_minimal_wav_bytes(duration_sec=est_duration)

        provenance = ArtifactProvenance(
            node_id=node_id,
            run_id=run_id,
            provider="mock",
            model="mock-omnivoice-v1",
            params={"text": text, "voiceId": voice_id, "tempo": tempo},
            input_hashes=[],
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        meta = ArtifactMeta(duration=est_duration)

        return self.store.store_bytes(
            data=wav_bytes,
            ext="wav",
            kind=ArtifactKind.AUDIO,
            provenance=provenance,
            meta=meta,
        )

    async def analyze_vision(
        self,
        media_uri: str,
        prompt: str,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Dict[str, Any]:
        return {
            "title": "Phân cảnh trích xuất từ video nguồn (Mock)",
            "overview": "Video hoạt hình 3D vui nhộn",
            "scenes": [
                {
                    "index": 1,
                    "title": "Cảnh 1: Sóc Nhỏ thức dậy",
                    "imagePrompt": "Sóc Nhỏ Bi vươn vai thức dậy trong căn phòng gỗ ấm cúng",
                    "videoPrompt": "Camera lia nhẹ từ trên xuống thấy Sóc Nhỏ mở mắt tươi cười",
                    "dialogue": "Oa, chào buổi sáng các bạn!",
                    "durationSec": 7.0,
                },
                {
                    "index": 2,
                    "title": "Cảnh 2: Gặp bạn Koala",
                    "imagePrompt": "Sóc Nhỏ và bạn Koala cùng ăn sáng",
                    "videoPrompt": "Bạn Koala vẫy tay chào và đưa cho Bi một chiếc bàn chải",
                    "dialogue": "Nhớ đánh răng trước khi đi chơi nha Bi!",
                    "durationSec": 8.0,
                },
            ],
        }

    async def text_complete(
        self,
        system: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Trợ lý theo quy tắc (Rule-based Assistant) khi ở chế độ chạy thử hoặc chưa có khóa API."""
        p_lower = prompt.lower().strip()
        actions: List[Dict[str, Any]] = []
        reply = (
            "[Chế độ chạy thử — Trợ lý quy tắc] Tôi đã nhận lệnh của bạn. "
            "Bạn có thể yêu cầu thêm bước kiểm tra, đổi tỉ lệ 16:9 / 9:16, chạy từ một cảnh/node, mở lịch đăng hoặc xem hồ sơ nhân vật."
        )
        requires_confirmation = False
        confirmation_meta: Optional[Dict[str, Any]] = None

        if any(k in p_lower for k in ["kiểm tra", "quality", "check", "gate"]):
            actions.append(
                {
                    "type": "add_node",
                    "nodeType": "quality_check",
                    "afterNodeType": "image_gen",
                    "beforeNodeType": "video_gen",
                    "summaryVi": "Đã thêm node Kiểm tra chất lượng (Gate) và nối giữa Tạo ảnh AI và Tạo video chuyển động",
                    "summaryEn": "Added Quality Check (Gate) node and wired between AI Image Gen and Video Gen",
                }
            )
            reply = (
                "[Chế độ chạy thử] Đã thêm node Kiểm tra chất lượng (Gate) sau bước Tạo ảnh AI và nối đầu ra sang Tạo video chuyển động."
            )
        elif "16:9" in p_lower or "9:16" in p_lower or "1:1" in p_lower or "4:5" in p_lower:
            ratio = "16:9" if "16:9" in p_lower else "1:1" if "1:1" in p_lower else "4:5" if "4:5" in p_lower else "9:16"
            actions.append(
                {
                    "type": "set_aspect_ratio",
                    "aspectRatio": ratio,
                    "summaryVi": f"Đã đổi tỉ lệ khung hình sang {ratio}",
                    "summaryEn": f"Changed aspect ratio to {ratio}",
                }
            )
            reply = f"[Chế độ chạy thử] Đã chuyển tỉ lệ khung hình của đồ thị và các node sinh sang {ratio}."
        elif any(k in p_lower for k in ["lên lịch", "schedule", "youtube", "tiktok"]) and any(
            t in p_lower for t in ["19:00", "20:00", "lên lịch", "schedule", "đăng"]
        ):
            if "mở lịch" in p_lower or "open schedule" in p_lower or "xem lịch" in p_lower:
                actions.append(
                    {
                        "type": "open_tab",
                        "tab": "publish",
                        "summaryVi": "Đã chuyển sang tab Lịch đăng & Kênh",
                        "summaryEn": "Opened Schedule & Channels tab",
                    }
                )
                reply = "[Chế độ chạy thử] Đã mở tab Lịch đăng & Kênh ở khung bên phải."
            else:
                platform = "tiktok" if "tiktok" in p_lower else "youtube"
                publish_time = "20:00" if "20:00" in p_lower else "19:00"
                requires_confirmation = True
                confirmation_meta = {
                    "kind": "publish",
                    "platform": platform,
                    "time": publish_time,
                    "episodeTitle": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
                }
                actions.append(
                    {
                        "type": "schedule_post",
                        "platform": platform,
                        "time": publish_time,
                        "episodeTitle": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
                        "summaryVi": f"Chuẩn bị lên lịch đăng Tập 1 lúc {publish_time} lên {platform.upper()} (chờ xác nhận)",
                        "summaryEn": f"Prepared schedule for Episode 1 at {publish_time} on {platform.upper()} (awaiting confirmation)",
                    }
                )
                reply = (
                    f"[Chế độ chạy thử] Lệnh đăng bài ra ngoài cần bạn xác nhận trước khi ghi lịch lên {platform.upper()} lúc {publish_time}."
                )
        elif any(k in p_lower for k in ["nhân vật", "koala", "sóc nhỏ", "soc nho", "character"]):
            char_id = "koala" if "koala" in p_lower else "soc_nho"
            actions.append(
                {
                    "type": "open_character",
                    "tab": "project",
                    "characterId": char_id,
                    "summaryVi": f"Đã mở hồ sơ nhân vật {'Bác sĩ Koala' if char_id == 'koala' else 'Sóc Nhỏ (Bi)'}",
                    "summaryEn": f"Opened character profile for {'Dr. Koala' if char_id == 'koala' else 'Little Squirrel (Bi)'}",
                }
            )
            reply = (
                f"[Chế độ chạy thử] Đã chuyển sang tab Dự án và mở hồ sơ đầy đủ của {'Bác sĩ Koala' if char_id == 'koala' else 'Sóc Nhỏ (Bi)'}."
            )
        elif any(k in p_lower for k in ["chạy", "run"]):
            requires_confirmation = True
            confirmation_meta = {
                "kind": "run",
                "mode": "downstream" if "từ" in p_lower or "from" in p_lower else "all",
                "estimatedCostUsd": 0.0,
            }
            actions.append(
                {
                    "type": "run_graph",
                    "mode": "downstream" if "từ" in p_lower or "from" in p_lower else "all",
                    "summaryVi": "Yêu cầu chạy đồ thị (chờ xác nhận chi phí)",
                    "summaryEn": "Requested graph run (awaiting cost confirmation)",
                }
            )
            reply = "[Chế độ chạy thử] Đã chuẩn bị lệnh chạy đồ thị. Vui lòng xác nhận trong hộp thoại chi phí để bắt đầu."
        elif any(k in p_lower for k in ["thêm node", "add node", "thêm bước", "giọng đọc", "tạo ảnh", "tạo video", "phụ đề"]):
            node_type = (
                "voice_tts"
                if "giọng" in p_lower
                else "captions"
                if "phụ đề" in p_lower
                else "video_gen"
                if "video" in p_lower
                else "image_gen"
            )
            actions.append(
                {
                    "type": "add_node",
                    "nodeType": node_type,
                    "summaryVi": f"Đã thêm node '{node_type}' vào đồ thị",
                    "summaryEn": f"Added '{node_type}' node to graph",
                }
            )
            reply = f"[Chế độ chạy thử] Đã thêm node '{node_type}' vào canvas."

        return {
            "reply": reply,
            "mode": "rule_based_mock",
            "actions": actions,
            "requiresConfirmation": requires_confirmation,
            "confirmationMeta": confirmation_meta,
        }
