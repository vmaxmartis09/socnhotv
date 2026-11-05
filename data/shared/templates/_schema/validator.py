#!/usr/bin/env python3
"""Validator cho Hợp đồng Template v2 (Session U — Tab Template).

Kiểm định cấu trúc template.json, ràng buộc ngữ nghĩa (verified phải có MP4 thật),
tính tương thích với composition.html.j2, styles.css, và sample.data.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

TEMPLATES_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TEMPLATES_DIR.parent.parent.parent

VALID_KINDS = {
    "animation",
    "film",
    "koc",
    "replace",
    "review",
    "remotion-style",
    "handdrawn",
    "formula",
    "fact",
    "cut",
    "slideshow",
    "talk",
    "reup",
    "story",
    "custom",
}

VALID_CATEGORIES = {
    "sales",
    "review",
    "reup",
    "animation",
    "education",
    "affiliate",
    "story",
}

VALID_STATUSES = {"draft", "runnable", "verified"}
VALID_TIERS = {"A", "B", "C"}
VALID_SLOT_TYPES = {
    "text",
    "media",
    "media[]",
    "product",
    "color",
    "number",
    "boolean",
    "character",
    "select",
}

KNOWN_NODE_TYPES = {
    "text",
    "script",
    "episode_script",
    "shot_images",
    "shot_videos",
    "voice_tts",
    "voice_multi",
    "captions",
    "hyperframes_render",
    "episode_render",
    "template_render",
    "platform_export",
    "export",
    "quality_check",
    "vision_analyze",
    "character",
    "image",
    "character_image",
    "scene",
    "transition",
    "source_video",
}


class ValidationError:
    def __init__(self, field: str, message: str, is_warning: bool = False):
        self.field = field
        self.message = message
        self.is_warning = is_warning

    def __repr__(self) -> str:
        prefix = "WARN" if self.is_warning else "ERROR"
        return f"[{prefix}] {self.field}: {self.message}"


def validate_template_dict(
    data: Dict[str, Any], template_dir: Optional[Path] = None
) -> Tuple[List[ValidationError], List[ValidationError]]:
    """Kiểm định toàn diện 1 dict template.json theo hợp đồng v2."""
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []

    def err(field: str, msg: str):
        errors.append(ValidationError(field, msg, is_warning=False))

    def warn(field: str, msg: str):
        warnings.append(ValidationError(field, msg, is_warning=True))

    # 1. Các trường bắt buộc v2
    required_v2 = [
        "id",
        "name",
        "version",
        "kind",
        "category",
        "status",
        "tier",
        "requires",
        "recipe",
        "slots",
        "outputs",
    ]
    for rf in required_v2:
        if rf not in data or data[rf] is None:
            err(rf, f"Thiếu trường bắt buộc '{rf}' trong template v2.")

    # 2. Kiểm định id
    tid = data.get("id")
    if tid is not None:
        if not isinstance(tid, str) or not re.match(r"^[a-z0-9-]+$", tid):
            err("id", f"ID '{tid}' không hợp lệ (phải là chuỗi kebab-case a-z0-9-).")

    # 3. Kiểm định name
    tname = data.get("name")
    if tname is not None and (not isinstance(tname, str) or len(tname.strip()) < 3):
        err("name", "Tên template phải là chuỗi tối thiểu 3 ký tự.")

    # 4. Kiểm định kind
    kind = data.get("kind")
    if kind is not None and kind not in VALID_KINDS:
        err("kind", f"Kind '{kind}' không hợp lệ. Phải thuộc: {sorted(VALID_KINDS)}")

    # 5. Kiểm định category
    cat = data.get("category")
    if cat is not None and cat not in VALID_CATEGORIES:
        err("category", f"Category '{cat}' không hợp lệ. Phải thuộc: {sorted(VALID_CATEGORIES)}")

    # 6. Kiểm định status
    status = data.get("status")
    if status is not None and status not in VALID_STATUSES:
        err("status", f"Status '{status}' không hợp lệ. Phải là: {sorted(VALID_STATUSES)}")

    # 7. Kiểm định tier
    tier = data.get("tier")
    if tier is not None and tier not in VALID_TIERS:
        err("tier", f"Tier '{tier}' không hợp lệ. Phải là 'A', 'B' hoặc 'C'.")

    # 8. Kiểm định requires
    requires = data.get("requires")
    if requires is not None:
        if not isinstance(requires, dict):
            err("requires", "'requires' phải là một object.")
        else:
            for sub in ("tools", "providers", "gpu", "ffmpeg"):
                if sub not in requires:
                    err(f"requires.{sub}", f"Thiếu trường 'requires.{sub}'.")
            if "tools" in requires and not isinstance(requires["tools"], list):
                err("requires.tools", "'requires.tools' phải là một danh sách string.")
            if "providers" in requires and not isinstance(requires["providers"], list):
                err("requires.providers", "'requires.providers' phải là một danh sách string.")
            if "gpu" in requires and not isinstance(requires["gpu"], bool):
                err("requires.gpu", "'requires.gpu' phải là boolean (true/false).")
            if "ffmpeg" in requires and not isinstance(requires["ffmpeg"], bool):
                err("requires.ffmpeg", "'requires.ffmpeg' phải là boolean (true/false).")

    # 9. Kiểm định recipe
    recipe = data.get("recipe")
    if recipe is not None:
        if isinstance(recipe, list):
            # Cho phép danh sách chuỗi node
            nodes = recipe
        elif isinstance(recipe, dict):
            nodes = recipe.get("nodes")
            if nodes is None or not isinstance(nodes, list):
                err("recipe.nodes", "'recipe.nodes' phải là một danh sách chuỗi mã node.")
                nodes = []
        else:
            err("recipe", "'recipe' phải là một object {nodes: [...]} hoặc list mã node.")
            nodes = []

        for idx, n in enumerate(nodes):
            if not isinstance(n, str) or not n.strip():
                err(f"recipe.nodes[{idx}]", f"Tên node không hợp lệ: {n}")
            elif n not in KNOWN_NODE_TYPES:
                warn(f"recipe.nodes[{idx}]", f"Node '{n}' chưa được đăng ký trong KNOWN_NODE_TYPES.")

    # 10. Kiểm định slots
    slots = data.get("slots")
    if slots is not None:
        if not isinstance(slots, list) or len(slots) == 0:
            err("slots", "'slots' phải là danh sách ít nhất 1 slot.")
        else:
            seen_keys = set()
            for idx, s in enumerate(slots):
                if not isinstance(s, dict):
                    err(f"slots[{idx}]", "Slot phải là một object.")
                    continue
                skey = s.get("key") or s.get("id")
                stype = s.get("type")
                if not skey or not isinstance(skey, str):
                    err(f"slots[{idx}].key", "Slot thiếu 'key' (chuỗi định danh).")
                elif skey in seen_keys:
                    err(f"slots[{idx}].key", f"Khóa slot trùng lặp: '{skey}'.")
                else:
                    seen_keys.add(skey)

                if not stype or not isinstance(stype, str):
                    err(f"slots[{idx}].type", "Slot thiếu 'type'.")
                elif stype not in VALID_SLOT_TYPES:
                    warn(f"slots[{idx}].type", f"Type '{stype}' chưa có trong danh sách chuẩn: {sorted(VALID_SLOT_TYPES)}")

    # 11. Kiểm định outputs
    outputs = data.get("outputs")
    if outputs is not None:
        if not isinstance(outputs, dict):
            err("outputs", "'outputs' phải là một object.")
        else:
            aspect = outputs.get("aspect")
            if not aspect or not isinstance(aspect, list) or len(aspect) == 0:
                err("outputs.aspect", "'outputs.aspect' phải là một danh sách tỉ lệ (vd: ['9:16']).")

    # 12. Kiểm định ngữ nghĩa cho trạng thái verified
    if status == "verified":
        sample_output = data.get("sample_output")
        verified_on = data.get("verified_on")

        if not sample_output:
            err("sample_output", "Template trạng thái 'verified' BẮT BUỘC có 'sample_output' trỏ tới file MP4 mẫu thật.")
        elif template_dir:
            mp4_path = template_dir / sample_output if not Path(sample_output).is_absolute() else Path(sample_output)
            if not mp4_path.exists() and (REPO_ROOT / sample_output).exists():
                mp4_path = REPO_ROOT / sample_output
            if not mp4_path.exists():
                err("sample_output", f"File sample_output không tồn tại trên đĩa: {mp4_path}")
            elif mp4_path.stat().st_size < 1000:
                err("sample_output", f"File sample_output quá nhỏ ({mp4_path.stat().st_size} bytes), nghi ngờ là file rỗng.")

        if not verified_on or not isinstance(verified_on, str) or not re.match(r"^\d{4}-\d{2}-\d{2}", verified_on):
            err("verified_on", "Template trạng thái 'verified' BẮT BUỘC có ngày 'verified_on' chuẩn YYYY-MM-DD.")

    # 13. Kiểm tra tệp đính kèm trong thư mục nếu có template_dir
    if template_dir and template_dir.is_dir():
        comp_file = template_dir / "composition.html.j2"
        if not comp_file.exists():
            err("files", f"Thiếu file 'composition.html.j2' trong {template_dir.name}")
        style_file = template_dir / "styles.css"
        if not style_file.exists():
            warn("files", f"Không tìm thấy file 'styles.css' trong {template_dir.name}")
        sample_data_file = template_dir / "sample.data.json"
        if not sample_data_file.exists():
            warn("files", f"Không tìm thấy 'sample.data.json' trong {template_dir.name}")

    return errors, warnings


def validate_template_file(template_json_path: Path) -> Tuple[List[ValidationError], List[ValidationError]]:
    """Đọc và validate 1 file template.json."""
    if not template_json_path.exists():
        return [ValidationError("file", f"Không tìm thấy file: {template_json_path}")], []

    try:
        data = json.loads(template_json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [ValidationError("json", f"Lỗi cú pháp JSON trong file: {e}")], []

    return validate_template_dict(data, template_dir=template_json_path.parent)


def validate_all_templates(templates_root: Path) -> Dict[str, Tuple[List[ValidationError], List[ValidationError]]]:
    """Quét và validate toàn bộ các thư mục template trong data/shared/templates/."""
    results: Dict[str, Tuple[List[ValidationError], List[ValidationError]]] = {}
    for entry in sorted(templates_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
            continue
        t_json = entry / "template.json"
        if t_json.exists():
            results[entry.name] = validate_template_file(t_json)
        else:
            results[entry.name] = (
                [ValidationError("file", f"Thư mục '{entry.name}' thiếu file template.json")],
                [],
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validator cho template v2 (SocNhoTV)")
    parser.add_argument("path", nargs="?", default=None, help="Đường dẫn thư mục hoặc file template.json cần kiểm tra")
    parser.add_argument("--all", action="store_true", help="Kiểm tra toàn bộ template trong data/shared/templates")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả định dạng JSON")

    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    if args.all or args.path is None:
        results = validate_all_templates(root)
    else:
        p = Path(args.path).resolve()
        if p.is_dir():
            results = {p.name: validate_template_file(p / "template.json")}
        else:
            results = {p.parent.name: validate_template_file(p)}

    total_count = len(results)
    pass_count = sum(1 for errs, _ in results.values() if len(errs) == 0)
    fail_count = total_count - pass_count

    if args.json:
        out = {
            "total": total_count,
            "passed": pass_count,
            "failed": fail_count,
            "details": {
                name: {
                    "valid": len(errs) == 0,
                    "errors": [{"field": e.field, "message": e.message} for e in errs],
                    "warnings": [{"field": w.field, "message": w.message} for w in warns],
                }
                for name, (errs, warns) in results.items()
            },
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if fail_count == 0 else 1

    # In báo cáo bảng
    print("=" * 70)
    print("BÁO CÁO KIỂM ĐỊNH HỢP ĐỒNG TEMPLATE V2 (SESSION U)")
    print("=" * 70)

    for name, (errs, warns) in results.items():
        if len(errs) == 0:
            status_tag = "✅ HỢP LỆ V2"
            if warns:
                status_tag += f" ({len(warns)} cảnh báo)"
            print(f"\n{name:30} {status_tag}")
        else:
            print(f"\n{name:30} ❌ KHÔNG ĐẠT ({len(errs)} lỗi)")
            for e in errs:
                print(f"    - [LỖI] {e.field}: {e.message}")
        for w in warns:
            print(f"    - [CẢNH BÁO] {w.field}: {w.message}")

    print("\n" + "-" * 70)
    print(f"Tổng số: {total_count} | Hợp lệ: {pass_count} | Không đạt: {fail_count}")
    print("=" * 70)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
