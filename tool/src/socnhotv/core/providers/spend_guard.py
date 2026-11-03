"""Khóa chi tiêu cứng đa tầng: trần dự án, trần 24 giờ, và trần riêng cho lệnh từ MCP/Agent."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from socnhotv.core.providers.errors import ProviderError, ProviderErrorKind

DEFAULT_CAP_USD = 5.0
DEFAULT_MCP_CAP_USD = 2.0


class SpendCapExceeded(ProviderError):
    """Ngoại lệ khi khoản chi vượt trần cho phép (không retry)."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            kind=ProviderErrorKind.SPEND_CAP,
            provider="spend_guard",
            retryable=False,
        )


class SpendGuard:
    """Sổ chi tiêu lưu ở data/projects/<id>/runs/spend.json.
    Hỗ trợ trần dự án (cap_usd), trần 24 giờ (daily_cap_usd) và trần MCP/Agent (mcp_cap_usd).
    """

    _lock = threading.Lock()

    def __init__(
        self,
        runs_dir: Path,
        cap_usd: float | None = None,
        daily_cap_usd: float | None = None,
        mcp_cap_usd: float | None = None,
    ):
        self.path = Path(runs_dir) / "spend.json"
        env_cap = os.environ.get("SOCNHOTV_SPEND_CAP_USD")
        self.cap = cap_usd if cap_usd is not None else (float(env_cap) if env_cap else DEFAULT_CAP_USD)

        env_daily = os.environ.get("SOCNHOTV_DAILY_CAP_USD")
        self.daily_cap = (
            daily_cap_usd
            if daily_cap_usd is not None
            else (float(env_daily) if env_daily else self.cap)
        )

        env_mcp = os.environ.get("SOCNHOTV_MCP_CAP_USD")
        self.mcp_cap = (
            mcp_cap_usd
            if mcp_cap_usd is not None
            else (float(env_mcp) if env_mcp else min(DEFAULT_MCP_CAP_USD, self.cap))
        )

    def _read_data(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"totalUsd": 0.0, "capUsd": self.cap, "entries": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"totalUsd": 0.0, "capUsd": self.cap, "entries": []}

    def spent(self) -> float:
        if not self.path.exists():
            return 0.0
        return float(self._read_data().get("totalUsd", 0.0))

    def spent_24h(self, now_ts: Optional[float] = None) -> float:
        """Tổng số tiền đã chi trong 24 giờ gần nhất."""
        if not self.path.exists():
            return 0.0
        now = now_ts if now_ts is not None else time.time()
        cutoff = now - 86400.0
        entries = self._read_data().get("entries", [])
        total = 0.0
        for e in entries:
            ts = e.get("ts")
            if ts is None or float(ts) >= cutoff:
                total += float(e.get("usd", 0.0))
        return round(max(0.0, total), 4)

    def spent_by_source_24h(self, source: str, now_ts: Optional[float] = None) -> float:
        """Tổng số tiền chi trong 24 giờ bởi một nguồn cụ thể (ví dụ: 'mcp')."""
        if not self.path.exists():
            return 0.0
        now = now_ts if now_ts is not None else time.time()
        cutoff = now - 86400.0
        entries = self._read_data().get("entries", [])
        total = 0.0
        for e in entries:
            if e.get("source") != source:
                continue
            ts = e.get("ts")
            if ts is None or float(ts) >= cutoff:
                total += float(e.get("usd", 0.0))
        return round(max(0.0, total), 4)

    def preview(self, amount: float, source: str = "api", now_ts: Optional[float] = None) -> Dict[str, Any]:
        """Kiểm tra trước khoản chi mà không ghi vào đĩa (phục vụ bước ước tính giá)."""
        total = self.spent()
        daily = self.spent_24h(now_ts=now_ts)
        mcp_spent = self.spent_by_source_24h("mcp", now_ts=now_ts)

        reason: Optional[str] = None
        if total + amount > self.cap + 1e-9:
            reason = f"Vượt trần chi tiêu dự án: đã chi ${total:.2f}, cần thêm ${amount:.2f}, trần ${self.cap:.2f}."
        elif daily + amount > self.daily_cap + 1e-9:
            reason = f"Vượt trần chi tiêu 24h: đã chi ${daily:.2f}, cần thêm ${amount:.2f}, trần ngày ${self.daily_cap:.2f}."
        elif source == "mcp" and mcp_spent + amount > self.mcp_cap + 1e-9:
            reason = f"Vượt trần chi tiêu MCP/Agent 24h: đã chi ${mcp_spent:.2f}, cần thêm ${amount:.2f}, trần MCP ${self.mcp_cap:.2f}."

        remaining = max(0.0, min(self.cap - total, self.daily_cap - daily))
        if source == "mcp":
            remaining = max(0.0, min(remaining, self.mcp_cap - mcp_spent))

        return {
            "canProceed": reason is None,
            "reason": reason,
            "requestedUsd": round(amount, 4),
            "projectSpentUsd": round(total, 4),
            "projectCapUsd": round(self.cap, 4),
            "dailySpentUsd": round(daily, 4),
            "dailyCapUsd": round(self.daily_cap, 4),
            "mcpSpentUsd": round(mcp_spent, 4),
            "mcpCapUsd": round(self.mcp_cap, 4),
            "remainingBudgetUsd": round(remaining, 4),
        }

    def reserve(
        self,
        amount: float,
        label: str,
        source: str = "api",
        now_ts: Optional[float] = None,
    ) -> None:
        """Ghi trước khoản sắp chi; ném SpendCapExceeded nếu vượt bất kỳ trần nào."""
        if amount <= 0:
            return
        with self._lock:
            now = now_ts if now_ts is not None else time.time()
            check = self.preview(amount, source=source, now_ts=now)
            if not check["canProceed"]:
                raise SpendCapExceeded(f"{check['reason']} ({label})")

            existing = self._read_data() if self.path.exists() else {"entries": []}
            total = float(existing.get("totalUsd", 0.0)) if self.path.exists() else 0.0
            entries = list(existing.get("entries", []))
            entries.append(
                {
                    "label": label,
                    "usd": round(amount, 4),
                    "source": source,
                    "ts": round(now, 3),
                }
            )
            data = {
                "totalUsd": round(total + amount, 4),
                "capUsd": self.cap,
                "dailyCapUsd": self.daily_cap,
                "mcpCapUsd": self.mcp_cap,
                "entries": entries,
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def refund(
        self,
        amount: float,
        label: str,
        source: str = "api",
        now_ts: Optional[float] = None,
    ) -> None:
        """Hoàn lại khi chắc chắn chưa tính phí (ví dụ lỗi xác thực/tham số trước khi gửi việc)."""
        if amount <= 0:
            return
        with self._lock:
            if not self.path.exists():
                return
            now = now_ts if now_ts is not None else time.time()
            data = self._read_data()
            data["totalUsd"] = round(max(0.0, float(data.get("totalUsd", 0.0)) - amount), 4)
            data.setdefault("entries", []).append(
                {
                    "label": f"hoàn: {label}",
                    "usd": -round(amount, 4),
                    "source": source,
                    "ts": round(now, 3),
                }
            )
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
