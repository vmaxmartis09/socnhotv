"""Cầu nối tới OmniVoice: chạy worker trong môi trường có `omnivoice` qua subprocess."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[4]
OMNIVOICE_DIR = PROJECT_ROOT / "integrations" / "OmniVoice"
WORKER = Path(__file__).resolve().with_name("omnivoice_worker.py")


def resolve_python() -> str:
    """OMNIVOICE_PYTHON > integrations/OmniVoice/.venv > interpreter hiện tại."""
    env = os.environ.get("OMNIVOICE_PYTHON")
    if env:
        return env
    venv_py = OMNIVOICE_DIR / ".venv" / "bin" / "python"
    return str(venv_py) if venv_py.exists() else sys.executable


class OmniVoiceEngine:
    def __init__(self, python_exe: Optional[str] = None):
        self.python_exe = python_exe or resolve_python()

    def _run(self, job: dict) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False)
            job_path = f.name
        try:
            res = subprocess.run([self.python_exe, str(WORKER), job_path], capture_output=True, text=True)
        finally:
            os.unlink(job_path)
        if res.returncode != 0:
            raise RuntimeError(f"OmniVoice lỗi:\n{res.stderr[-1500:]}")
        return res.stdout

    def create_prompt(self, profile_dir: str, ref_slice: str, ref_text: str) -> str:
        prompt_file = str(Path(profile_dir) / "omnivoice_prompt.pt")
        self._run({"mode": "prompt", "ref_audio": ref_slice, "ref_text": ref_text, "prompt_out": prompt_file})
        return prompt_file

    def synthesize(
        self,
        profile_dir: str,
        sentences: List[str],
        output_wav: str,
        speed: float = 1.0,
        num_step: int = 32,
    ) -> str:
        p = Path(profile_dir)
        ref_txt = p / "reference_transcript.txt"
        self._run({
            "mode": "synth",
            "prompt": str(p / "omnivoice_prompt.pt"),
            "ref_audio": str(p / "reference_clean_slice.wav"),
            "ref_text": ref_txt.read_text(encoding="utf-8").strip() if ref_txt.exists() else None,
            "sentences": sentences,
            "output_wav": output_wav,
            "speed": speed,
            "num_step": num_step,
        })
        return output_wav
