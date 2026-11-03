"""Khóa chi tiêu cứng: cộng dồn chi phí ước tính của mọi lần gọi trả phí, từ chối khi vượt trần."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

DEFAULT_CAP_USD = 5.0


class SpendCapExceeded(Exception):
    pass


class SpendGuard:
    """Sổ chi tiêu lưu ở data/projects/<id>/runs/spend.json. Trần mặc định 5 đô cho cả dự án."""

    _lock = threading.Lock()

    def __init__(self, runs_dir: Path, cap_usd: float | None = None):
        self.path = Path(runs_dir) / "spend.json"
        env = os.environ.get("SOCNHOTV_SPEND_CAP_USD")
        self.cap = cap_usd if cap_usd is not None else (float(env) if env else DEFAULT_CAP_USD)

    def spent(self) -> float:
        if not self.path.exists():
            return 0.0
        return float(json.loads(self.path.read_text(encoding="utf-8")).get("totalUsd", 0.0))

    def reserve(self, amount: float, label: str) -> None:
        """Ghi trước khoản sắp chi; ném lỗi nếu tổng vượt trần. Không hoàn lại khi gọi thất bại (an toàn)."""
        with self._lock:
            total = self.spent()
            if total + amount > self.cap + 1e-9:
                raise SpendCapExceeded(
                    f"Vượt trần chi tiêu: đã chi ${total:.2f}, cần thêm ${amount:.2f} cho {label}, trần ${self.cap:.2f}."
                )
            data = {"totalUsd": round(total + amount, 4), "capUsd": self.cap, "entries": []}
            if self.path.exists():
                data["entries"] = json.loads(self.path.read_text(encoding="utf-8")).get("entries", [])
            data["entries"].append({"label": label, "usd": round(amount, 4)})
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def refund(self, amount: float, label: str) -> None:
        """Hoàn lại khi chắc chắn chưa tính phí (ví dụ lỗi xác thực trước khi gửi việc)."""
        with self._lock:
            if not self.path.exists():
                return
            data = json.loads(self.path.read_text(encoding="utf-8"))
            data["totalUsd"] = round(max(0.0, data["totalUsd"] - amount), 4)
            data["entries"].append({"label": f"hoàn: {label}", "usd": -round(amount, 4)})
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
