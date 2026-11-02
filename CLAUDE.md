# SocNhoTV

Project độc lập, clone từ gobi-social: toàn bộ skill, rule, workflow, agent và tool làm video.

- Skills: `.agents/skills` (`.claude/skills` trỏ vào đây), rules/workflows: `.agents/`, `.agent/`, `AGENTS.md`
- Tool video: `src/gobi/services/media/` (HyperFramesEngine, video_engine, render_*, snaptik), `tools/video/`, `scripts/video/`, `scripts/flow_ai/`
- Chuẩn hậu kỳ: `docs/HYPERFRAMES_POST_PRODUCTION_STANDARD.md`
- Quy trình: luôn dùng HyperFrames cho edit/caption/overlay/audio ducking/render 9:16; không hardcode đường dẫn tuyệt đối.
- Nhân vật Sóc Nhỏ: voiceover luôn dùng voice-id `soc-nho` (`assets/voice_vault/soc-nho/`, skill `vietnamese-voice-clone`) trong mọi video dựng bằng HyperFrames; profile nhân vật ở `assets/soc_nho/soc_nho_profile.json`.
