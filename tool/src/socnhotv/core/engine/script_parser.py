from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def _count_words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def _estimate_scene_duration(dialogue: str, word_count: int, default_dur: float = 6.0) -> float:
    """Ước lượng thời lượng cảnh dựa trên tốc độ nói tiếng Việt (~3 từ/giây)."""
    if word_count > 0:
        # 3 từ/giây + 1.2s thở/ngắt nhịp
        est = (word_count / 3.0) + 1.2
        return round(max(3.5, min(est, 15.0)), 1)
    return round(default_dur, 1)


def parse_script(
    raw_script: str,
    target_scene_count: int = 6,
    target_duration_sec: float = 45.0,
) -> List[Dict[str, Any]]:
    """Phân tích kịch bản tất định từ văn bản thuần (Deterministic Script Parser).
    
    Hỗ trợ:
    - Ngăn cảnh bằng 'Cảnh N:', 'Scene N:', 'Phân cảnh N:'
    - Ngăn cảnh bằng đường kẻ '---', '===', '***'
    - Ngăn cảnh bằng dòng trống kép (paragraphs)
    - Kịch bản một đoạn không ngăn -> tự động tách theo câu và độ dài
    - Nhận diện lời thoại đa nhân vật dạng 'Tên: Lời thoại' hoặc '[Tên]: Lời thoại'
    - Nhận diện hành động trong ngoặc đơn (Mô tả hành động)
    - Nhận diện chỉ dẫn camera / hình ảnh dạng 'Hình ảnh:', 'Camera:', 'Video:'
    """
    if not raw_script or not raw_script.strip():
        return []

    text = raw_script.strip()

    # 1. Phát hiện các khối cảnh (Scene Chunks)
    chunks: List[Tuple[Optional[str], str]] = []  # List of (header_title, content)

    # Regex nhận diện tiêu đề cảnh ở đầu dòng
    header_pattern = re.compile(
        r"^(?:[#*>\s]*)"
        r"(?:(?:Cảnh|Phân cảnh|Hồi|Scene|Part|Segment)\s+(\d+|[IVXLCDM]+)[\s:.-]*(.*))$",
        re.IGNORECASE | re.MULTILINE,
    )

    headers = list(header_pattern.finditer(text))

    if len(headers) >= 2 or (len(headers) == 1 and headers[0].start() == 0):
        # Tách theo header
        for i, match in enumerate(headers):
            start = match.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            chunk_raw = text[start:end].strip()
            
            # Tiêu đề từ header line
            line_break = chunk_raw.find("\n")
            if line_break != -1:
                header_line = chunk_raw[:line_break].strip()
                content = chunk_raw[line_break + 1:].strip()
            else:
                header_line = chunk_raw
                content = ""
            
            # Làm sạch header_line
            header_clean = re.sub(r"^[#*>\s]+", "", header_line).strip()
            chunks.append((header_clean, content))

    elif re.search(r"^[ \t]*[-=_*~]{3,}[ \t]*$", text, re.MULTILINE):
        # Tách theo đường kẻ ngang --- hoặc ===
        raw_chunks = re.split(r"^[ \t]*[-=_*~]{3,}[ \t]*$", text, flags=re.MULTILINE)
        for rc in raw_chunks:
            rc_s = rc.strip()
            if rc_s:
                chunks.append((None, rc_s))

    elif "\n\n" in text:
        # Tách theo đoạn trống kép
        raw_chunks = [c.strip() for c in re.split(r"\n\s*\n+", text) if c.strip()]
        for rc in raw_chunks:
            chunks.append((None, rc))

    else:
        # Kịch bản 1 đoạn dài không có ngắt dòng kép
        # Tách theo câu và gom thành ~target_scene_count cảnh
        sentence_endings = re.compile(r"(?<=[.!?…])\s+(?=[A-Z\u00C0-\u1EF90-9])")
        sentences = [s.strip() for s in sentence_endings.split(text) if s.strip()]
        
        target = max(1, min(target_scene_count, len(sentences)))
        if target > 1 and len(sentences) >= target:
            # Gom đều các câu vào target nhóm
            chunk_size = len(sentences) / target
            for idx in range(target):
                s_idx = int(idx * chunk_size)
                e_idx = int((idx + 1) * chunk_size) if idx < target - 1 else len(sentences)
                grouped = " ".join(sentences[s_idx:e_idx]).strip()
                if grouped:
                    chunks.append((None, grouped))
        else:
            chunks.append((None, text))

    # Nếu vẫn không có chunk nào
    if not chunks:
        chunks = [(None, text)]

    # 2. Xử lý chi tiết từng cảnh
    scenes: List[Dict[str, Any]] = []
    
    # Từ khóa chỉ dẫn hình ảnh/camera không phải là lời thoại nhân vật
    directive_prefixes = {
        "mô tả", "hinh anh", "hình ảnh", "visual", "image", "image prompt", "prompt",
        "video", "camera", "action", "hành động", "góc quay", "bối cảnh", "note", "ghi chú"
    }

    dialogue_line_pattern = re.compile(
        r"^(?:[#*>\s-]*)"
        r"(?:\[([^\]]+)\]|([A-Za-z0-9_\u00C0-\u1EF9\s]+?))"
        r"\s*[:：]\s*(.+)$"
    )

    for idx, (header_title, chunk_content) in enumerate(chunks, start=1):
        lines = [ln.strip() for ln in chunk_content.splitlines() if ln.strip()]
        
        dialogues: List[str] = []
        visual_parts: List[str] = []
        camera_parts: List[str] = []
        
        for line in lines:
            # Kiểm tra dòng chỉ dẫn trong ngoặc (hành động/camera)
            if (line.startswith("(") and line.endswith(")")) or (line.startswith("[") and line.endswith("]")):
                inner = line[1:-1].strip()
                if any(inner.lower().startswith(p) for p in ("camera", "goc quay", "góc quay", "zoom", "pan", "dolly")):
                    camera_parts.append(inner)
                else:
                    visual_parts.append(inner)
                continue

            # Kiểm tra định dạng Tên: Lời thoại hoặc Chỉ dẫn: Nội dung
            m = dialogue_line_pattern.match(line)
            if m:
                speaker = (m.group(1) or m.group(2) or "").strip()
                content = m.group(3).strip()
                speaker_norm = speaker.lower()

                if speaker_norm in directive_prefixes:
                    if speaker_norm in ("camera", "góc quay", "video"):
                        camera_parts.append(content)
                    else:
                        visual_parts.append(content)
                else:
                    # Lời thoại thật của nhân vật
                    dialogues.append(f"{speaker}: {content}")
            else:
                # Dòng mô tả bình thường
                visual_parts.append(line)

        # Xây dựng các trường cho cảnh
        title = header_title if header_title else f"Cảnh {idx}"
        
        # Thoại gộp
        full_dialogue = "\n".join(dialogues) if dialogues else ""
        
        # Mô tả ảnh
        if visual_parts:
            image_prompt = ". ".join(visual_parts)
        elif full_dialogue:
            # Tự tổng hợp mô tả từ lời thoại
            first_dlg = dialogues[0]
            image_prompt = f"Cảnh hoạt hình 3D: {first_dlg}"
        else:
            image_prompt = f"Phân cảnh hoạt hình 3D cho {title}"

        # Mô tả chuyển động / camera
        if camera_parts:
            video_prompt = ". ".join(camera_parts)
        else:
            video_prompt = f"Camera góc trung chuyển động mượt mà, diễn hoạt sinh động theo nội dung {title}"

        # Ước lượng thời lượng
        total_words = _count_words(full_dialogue)
        duration_sec = _estimate_scene_duration(full_dialogue, total_words)

        scenes.append({
            "sceneNumber": idx,
            "title": title,
            "imagePrompt": image_prompt,
            "videoPrompt": video_prompt,
            "dialogue": full_dialogue,
            "durationSec": duration_sec,
        })

    # Cân chỉnh tổng thời lượng nếu người dùng chỉ định target_duration_sec
    if scenes and target_duration_sec > 0:
        current_total = sum(s["durationSec"] for s in scenes)
        if current_total > 0 and abs(current_total - target_duration_sec) > 10:
            scale = target_duration_sec / current_total
            for s in scenes:
                scaled = round(s["durationSec"] * scale, 1)
                s["durationSec"] = max(3.0, min(scaled, 20.0))

    return scenes
