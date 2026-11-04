from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

from socnhotv.video.contracts import Platform, RenderRequest
from socnhotv.video.platforms import PLATFORMS, list_platforms
from socnhotv.video.queue import get_render_queue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("socnhotv.video.cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m socnhotv.video.cli",
        description="SocNhoTV Video CLI — Render video HyperFrames đa nền tảng",
    )
    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực thi")

    # Lệnh platforms
    subparsers.add_parser("platforms", help="Liệt kê các nền tảng hỗ trợ")

    # Lệnh render
    render_parser = subparsers.add_parser("render", help="Khởi chạy render video qua RenderQueue")
    render_parser.add_argument("--project", "-p", default="soc-nho-tv", help="ID project (mặc định: soc-nho-tv)")
    render_parser.add_argument("--template", "-t", required=True, help="ID template (ví dụ: tiktok-sales-v1)")
    render_parser.add_argument("--platforms", default="tiktok", help="Danh sách nền tảng ngăn cách bằng dấu phẩy (vd: tiktok,youtube)")
    render_parser.add_argument("--data", "-d", required=True, help="Đường dẫn file JSON hoặc chuỗi JSON dữ liệu slot")
    render_parser.add_argument("--output-name", "-o", default=None, help="Tên thư mục output (mặc định sinh tự động)")
    render_parser.add_argument("--wait", action="store_true", default=True, help="Chờ render xong và in kết quả")

    return parser


def handle_platforms():
    print(f"\n{'ID':<12} | {'Tên':<18} | {'Kích thước':<12} | {'Aspect':<8} | {'Safe Zone (T/B/L/R)':<20}")
    print("-" * 75)
    for p in list_platforms():
        sz = f"{p.safe_zone.top}/{p.safe_zone.bottom}/{p.safe_zone.left}/{p.safe_zone.right}"
        print(f"{p.id:<12} | {p.name:<18} | {f'{p.width}x{p.height}':<12} | {p.aspect_ratio:<8} | {sz:<20}")
    print()


def handle_render(args: argparse.Namespace):
    # Parse data
    data_input = args.data
    data_dict: Dict[str, Any] = {}
    data_path = Path(data_input)
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            data_dict = json.load(f)
    else:
        try:
            data_dict = json.loads(data_input)
        except Exception as e:
            logger.error(f"Không thể đọc JSON từ --data: {e}")
            sys.exit(1)

    platforms_list: List[Platform] = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]  # type: ignore
    for p in platforms_list:
        if p not in PLATFORMS:
            logger.error(f"Nền tảng '{p}' không hợp lệ. Chọn từ: {list(PLATFORMS.keys())}")
            sys.exit(1)

    output_name = args.output_name or f"render_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    req = RenderRequest(
        project_id=args.project,
        template_id=args.template,
        platforms=platforms_list,
        data=data_dict,
        output_name=output_name,
    )

    queue = get_render_queue()
    job = queue.submit(req)
    logger.info(f"Đã đưa job vào hàng đợi: {job.job_id} (Project: {args.project}, Platforms: {platforms_list})")

    if not args.wait:
        print(json.dumps(job.model_dump(), indent=2, ensure_ascii=False))
        return

    # Chờ hoàn thành
    logger.info("Đang chờ hoàn thành tiến trình render...")
    while True:
        current_job = queue.get(args.project, job.job_id)
        if current_job.status in ("done", "failed"):
            print("\n" + "=" * 60)
            print(f"Trạng thái: {current_job.status.upper()}")
            if current_job.status == "done":
                print("Outputs:")
                for plat, path in current_job.outputs.items():
                    print(f"  • {plat}: {path}")
            else:
                print(f"Lỗi: {current_job.error}")
            print("=" * 60 + "\n")
            if current_job.status == "failed":
                sys.exit(1)
            break
        time.sleep(1.0)


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "platforms":
        handle_platforms()
    elif args.command == "render":
        handle_render(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
