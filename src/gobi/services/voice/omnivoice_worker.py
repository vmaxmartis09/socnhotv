"""Chạy BÊN TRONG môi trường có `omnivoice` (integrations/OmniVoice). Không import gì từ gobi.

Dùng:  python omnivoice_worker.py <job.json>
job.json:
  {"mode": "prompt", "ref_audio": ..., "ref_text": ..., "prompt_out": ...}
  {"mode": "synth", "prompt": ..., "ref_audio": ..., "ref_text": ..., "sentences": [...],
   "output_wav": ..., "speed": 1.0, "num_step": 32, "pause_sec": 0.18}
"""

import json
import sys

import numpy as np
import soundfile as sf
import torch

SAMPLE_RATE = 24000


def pick_device():
    if torch.backends.mps.is_available():
        return "mps", torch.float16
    if torch.cuda.is_available():
        return "cuda:0", torch.float16
    return "cpu", torch.float32


def load_model():
    from omnivoice import OmniVoice

    device, dtype = pick_device()
    return OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map=device,
        dtype=dtype,
        asr_model_name="openai/whisper-small",
        asr_device="cpu",
    )


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        job = json.load(f)

    from pathlib import Path

    from omnivoice import VoiceClonePrompt

    model = load_model()

    if job["mode"] == "prompt":
        prompt = model.create_voice_clone_prompt(ref_audio=job["ref_audio"], ref_text=job["ref_text"])
        prompt.save(job["prompt_out"])
        print("PROMPT_SAVED:" + job["prompt_out"])
        return

    prompt_path = Path(job["prompt"])
    if prompt_path.exists():
        prompt = VoiceClonePrompt.load(str(prompt_path))
    else:
        prompt = model.create_voice_clone_prompt(ref_audio=job["ref_audio"], ref_text=job["ref_text"])
        prompt.save(str(prompt_path))

    gap = np.zeros(int(job.get("pause_sec", 0.18) * SAMPLE_RATE), dtype=np.float32)
    parts = []
    for i, sentence in enumerate(job["sentences"], 1):
        audio = model.generate(
            text=sentence,
            language="vi",
            voice_clone_prompt=prompt,
            speed=job.get("speed", 1.0),
            denoise=True,
            num_step=job.get("num_step", 32),
        )
        parts.append(np.asarray(audio[0], dtype=np.float32).reshape(-1))
        parts.append(gap)
        print(f"SYNTH {i}/{len(job['sentences'])}", flush=True)

    sf.write(job["output_wav"], np.concatenate(parts[:-1]), SAMPLE_RATE)
    print("SYNTH_DONE:" + job["output_wav"])


if __name__ == "__main__":
    main()
