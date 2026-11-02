"""Tiền xử lý mẫu giọng: trích audio + lọc nhiễu -> cắt lát vàng trọn câu -> chép lời tiếng Việt."""

import os
import subprocess
from typing import List, Optional

import imageio_ffmpeg
import numpy as np
import soundfile as sf

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class AudioPreprocessor:
    def __init__(self, whisper_model: str = "base"):
        self.whisper_model_name = whisper_model
        self._whisper = None

    def _get_whisper(self):
        if self._whisper is None:
            from faster_whisper import WhisperModel

            print(f"[AudioPreprocessor] Tải Faster-Whisper ({self.whisper_model_name})...")
            self._whisper = WhisperModel(self.whisper_model_name, device="cpu", compute_type="int8")
        return self._whisper

    def extract_and_denoise_audio(self, input_path: str, output_wav: str, sample_rate: int = 48000) -> str:
        """ffmpeg: mono, band-pass 80Hz-12kHz, afftdn giảm nhiễu nền."""
        os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)
        cmd = [
            FFMPEG_EXE, "-y", "-i", str(input_path), "-vn",
            "-af", "highpass=f=80,lowpass=f=12000,afftdn=nf=-25",
            "-ar", str(sample_rate), "-ac", "1", str(output_wav),
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Không trích xuất được audio từ {input_path}: {res.stderr[-400:]}")
        return output_wav

    def _load_16k(self, audio_path: str) -> np.ndarray:
        cmd = [FFMPEG_EXE, "-y", "-i", str(audio_path), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return np.frombuffer(raw, dtype=np.float32)

    def transcribe_segments(self, audio_path: str, language: str = "vi") -> List[dict]:
        """Whisper + VAD, trả về các câu kèm mốc thời gian."""
        segments, _ = self._get_whisper().transcribe(
            self._load_16k(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        return [
            {"start": float(s.start), "end": float(s.end), "text": s.text.strip()}
            for s in segments
            if s.text.strip()
        ]

    def transcribe_audio(self, audio_path: str, language: str = "vi") -> str:
        return " ".join(s["text"] for s in self.transcribe_segments(audio_path, language)).strip()

    @staticmethod
    def _rms(data: np.ndarray) -> float:
        return float(np.sqrt(np.mean(data**2))) if len(data) else 0.0

    def _pick_sentence_slice(self, data, sr, segments, target, lo, hi) -> Optional[dict]:
        """Ghép các câu liên tiếp thành lát lo..hi giây, bắt đầu và kết thúc đúng ranh giới câu."""
        best, best_score = None, -1e9
        for i in range(len(segments)):
            start, end, texts = segments[i]["start"], segments[i]["end"], [segments[i]["text"]]
            j = i
            while True:
                dur = end - start
                if lo <= dur <= hi:
                    chunk = data[int(start * sr):int(end * sr)]
                    rms = self._rms(chunk)
                    if 0.03 <= rms <= 0.55 and np.max(np.abs(chunk)) < 0.99:
                        score = rms * 10.0 - abs(dur - target)
                        if score > best_score:
                            best_score = score
                            best = {"start": start, "end": end, "text": " ".join(texts)}
                if dur >= hi or j + 1 >= len(segments) or segments[j + 1]["start"] - end > 0.6:
                    break
                j += 1
                end = segments[j]["end"]
                texts.append(segments[j]["text"])
        return best

    def _energy_window(self, data, sr, target) -> tuple:
        """Phương án dự phòng khi không có câu phù hợp: cửa sổ RMS ổn định nhất."""
        n, step = int(target * sr), int(0.2 * sr)
        if len(data) <= n:
            return 0, len(data)
        best, best_start = -1e9, 0
        for s in range(0, len(data) - n, step):
            w = data[s:s + n]
            rms = self._rms(w)
            if rms < 0.03 or rms > 0.55:
                continue
            zcr = np.sum(np.abs(np.diff(np.sign(w)))) / (2.0 * len(w))
            score = rms * 15.0 - abs(zcr - 0.12) * 8.0 - abs(np.max(np.abs(w)) / (rms + 1e-6) - 4.0) * 1.5
            if score > best:
                best, best_start = score, s
        return best_start, best_start + n

    def process_media(
        self,
        input_media_path: str,
        output_dir: str,
        target_duration: float = 4.5,
        custom_transcript: Optional[str] = None,
        min_duration: float = 3.5,
        max_duration: float = 6.0,
    ) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        full_wav = os.path.join(output_dir, "raw_extracted_clean.wav")
        slice_wav = os.path.join(output_dir, "reference_clean_slice.wav")

        print(f"[1/3] Trích xuất + khử nhiễu: {input_media_path}")
        self.extract_and_denoise_audio(input_media_path, full_wav)
        data, sr = sf.read(full_wav)
        if data.ndim > 1:
            data = data[:, 0]

        print(f"[2/3] Tìm lát vàng ~{target_duration}s kết thúc ở ranh giới câu")
        transcript = custom_transcript.strip() if custom_transcript else None
        picked = None
        if not transcript:
            segs = self.transcribe_segments(full_wav)
            picked = self._pick_sentence_slice(data, sr, segs, target_duration, min_duration, max_duration)

        if picked:
            s, e = int(picked["start"] * sr), int(picked["end"] * sr)
            transcript = picked["text"]
        else:
            s, e = self._energy_window(data, sr, target_duration)
        piece = data[s:e].copy()
        fade = min(int(0.03 * sr), len(piece) // 2)
        if fade > 0:
            piece[:fade] *= np.linspace(0, 1, fade)
            piece[-fade:] *= np.linspace(1, 0, fade)
        sf.write(slice_wav, piece, sr)

        if not transcript:
            print("[3/3] Whisper chép lời lát cắt")
            transcript = self.transcribe_audio(slice_wav)
        else:
            print("[3/3] Dùng transcript khớp lát cắt")

        result = {
            "full_wav": full_wav,
            "ref_slice_wav": slice_wav,
            "start_sec": round(s / sr, 3),
            "end_sec": round(e / sr, 3),
            "duration": round(len(piece) / sr, 3),
            "rms": round(self._rms(piece), 4),
            "transcript": transcript,
        }
        print(f"    Lát vàng {result['duration']}s: \"{transcript}\"")
        return result
