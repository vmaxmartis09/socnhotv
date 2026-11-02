import React from 'react';
import { SceneItem, Character, TransitionType } from '../types';

interface SceneCardProps {
  scene: SceneItem;
  characters: Character[];
  globalLockVerbatim: boolean;
  onUpdate: (updated: SceneItem) => void;
  onGenerateImage: (scene: SceneItem) => void;
  onGenerateVideo: (scene: SceneItem) => void;
  onDelete: (id: string) => void;
  isBatchRunning: boolean;
}

export const SceneCard: React.FC<SceneCardProps> = ({
  scene,
  characters,
  globalLockVerbatim,
  onUpdate,
  onGenerateImage,
  onGenerateVideo,
  onDelete,
  isBatchRunning,
}) => {
  // Check which characters are detected and ready
  const matchedChars = characters.filter((c) =>
    scene.detectedCharacters.includes(c.name)
  );

  const transitionType = scene.transition?.type || 'cut';
  const transitionSec = scene.transition?.seconds ?? 0.5;
  const isLocked = globalLockVerbatim || Boolean(scene.locked);

  const handleTransitionTypeChange = (type: TransitionType) => {
    onUpdate({
      ...scene,
      transition: {
        type,
        seconds: transitionSec,
      },
    });
  };

  const handleTransitionSecChange = (seconds: number) => {
    onUpdate({
      ...scene,
      transition: {
        type: transitionType,
        seconds,
      },
    });
  };

  const handleToggleLock = () => {
    if (globalLockVerbatim) return; // controlled globally
    onUpdate({
      ...scene,
      locked: !scene.locked,
    });
  };

  return (
    <div className="bg-[#181a20] border border-[#2e323b] rounded-xl p-3.5 flex flex-col gap-3 transition-colors hover:border-[#414757]">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center justify-center font-mono font-bold text-xs">
            {scene.sceneIndex < 10 ? `0${scene.sceneIndex}` : scene.sceneIndex}
          </span>
          <span className="font-semibold text-slate-200 text-xs">
            Cảnh #{scene.sceneIndex}
          </span>

          {/* Locked Badge / Toggle */}
          <button
            onClick={handleToggleLock}
            disabled={globalLockVerbatim || isBatchRunning}
            title={
              globalLockVerbatim
                ? 'Đang bật Khóa nguyên văn cho tất cả cảnh'
                : isLocked
                ? 'Đang khóa nguyên văn: Gửi prompt chính xác, không nối style bible'
                : 'Bấm để khóa nguyên văn prompt cảnh này'
            }
            className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 border transition-colors ${
              isLocked
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-[#12141a] text-slate-400 border-[#2d313d] hover:border-slate-500'
            }`}
          >
            <span className="material-symbols-outlined text-[13px]">
              {isLocked ? 'lock' : 'lock_open'}
            </span>
            <span>{isLocked ? 'Khóa nguyên văn' : 'Tự do'}</span>
          </button>
        </div>

        {/* Status Pills */}
        <div className="flex items-center gap-2">
          {/* Image status badge */}
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-medium flex items-center gap-1 ${
              scene.imageStatus === 'ready'
                ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/40'
                : scene.imageStatus === 'generating'
                ? 'bg-amber-950/60 text-amber-300 border border-amber-800/40 animate-pulse'
                : scene.imageStatus === 'error'
                ? 'bg-rose-950/60 text-rose-300 border border-rose-800/40'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            <span className="material-symbols-outlined text-[12px]">image</span>
            <span>
              {scene.imageStatus === 'ready'
                ? 'Ảnh sẵn sàng'
                : scene.imageStatus === 'generating'
                ? 'Đang tạo ảnh'
                : scene.imageStatus === 'error'
                ? 'Lỗi ảnh'
                : 'Chờ tạo ảnh'}
            </span>
          </span>

          {/* Video status badge */}
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-medium flex items-center gap-1 ${
              scene.videoStatus === 'ready'
                ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/40'
                : scene.videoStatus === 'generating'
                ? 'bg-amber-950/60 text-amber-300 border border-amber-800/40 animate-pulse'
                : scene.videoStatus === 'error'
                ? 'bg-rose-950/60 text-rose-300 border border-rose-800/40'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            <span className="material-symbols-outlined text-[12px]">movie</span>
            <span>
              {scene.videoStatus === 'ready'
                ? 'Video sẵn sàng'
                : scene.videoStatus === 'generating'
                ? 'Đang tạo video'
                : scene.videoStatus === 'error'
                ? 'Lỗi video'
                : 'Chờ video'}
            </span>
          </span>

          <button
            onClick={() => onDelete(scene.id)}
            disabled={isBatchRunning}
            className="text-slate-500 hover:text-rose-400 p-1 rounded transition-colors disabled:opacity-30"
            title="Xóa cảnh"
          >
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      </div>

      {/* Detected Characters */}
      <div className="flex flex-wrap items-center gap-1.5 bg-[#12141a] p-2 rounded-lg border border-[#242832]">
        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1 mr-1">
          <span className="material-symbols-outlined text-[14px]">face</span>
          <span>Nhân vật:</span>
        </span>
        {matchedChars.length > 0 ? (
          matchedChars.map((c) => (
            <span
              key={c.id}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] bg-amber-400/10 text-amber-300 border border-amber-400/20"
            >
              {c.base64 && (
                <img
                  src={`data:${c.mimeType || 'image/png'};base64,${c.base64}`}
                  alt={c.name}
                  className="w-3.5 h-3.5 rounded-full object-cover"
                />
              )}
              <span>{c.name}</span>
            </span>
          ))
        ) : (
          <span className="text-[11px] text-slate-500 italic">
            (Chưa nhận diện được tên nhân vật nào trong prompt)
          </span>
        )}
      </div>

      {/* Prompt Editors */}
      <div className="space-y-2">
        <div>
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1 mb-1">
            <span className="material-symbols-outlined text-[12px] text-amber-400">photo_camera</span>
            <span>Prompt ảnh (bối cảnh & khung hình đầu)</span>
          </label>
          <textarea
            value={scene.imagePrompt}
            onChange={(e) => onUpdate({ ...scene, imagePrompt: e.target.value })}
            disabled={isBatchRunning}
            rows={2}
            className="w-full bg-[#0d0f14] border border-[#272b36] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400 resize-none disabled:opacity-60"
            placeholder="Mô tả hình ảnh khung cảnh, góc máy..."
          />
        </div>

        <div>
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1 mb-1">
            <span className="material-symbols-outlined text-[12px] text-cyan-400">videocam</span>
            <span>Prompt video (chuyển động & diễn xuất)</span>
          </label>
          <textarea
            value={scene.videoPrompt}
            onChange={(e) => onUpdate({ ...scene, videoPrompt: e.target.value })}
            disabled={isBatchRunning}
            rows={2}
            className="w-full bg-[#0d0f14] border border-[#272b36] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 resize-none disabled:opacity-60"
            placeholder="Mô tả hành động của nhân vật, camera chuyển động..."
          />
        </div>
      </div>

      {/* Mục 4: Chọn chuyển cảnh sang cảnh tiếp theo */}
      <div className="bg-[#12141b] border border-[#262a36] rounded-lg p-2 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-1.5 text-slate-400 font-semibold text-[11px]">
          <span className="material-symbols-outlined text-[15px] text-amber-400">shuffle</span>
          <span>Chuyển cảnh tiếp theo:</span>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={transitionType}
            onChange={(e) => handleTransitionTypeChange(e.target.value as TransitionType)}
            disabled={isBatchRunning}
            className="bg-[#0b0c10] border border-[#2d313e] rounded px-2 py-1 text-slate-200 text-[11px] focus:outline-none focus:border-amber-400"
          >
            <option value="cut">Cut (Cắt ngay)</option>
            <option value="fade">Fade (Mờ dần)</option>
            <option value="dissolve">Dissolve (Hòa tan)</option>
            <option value="wipe">Wipe (Gạt cảnh)</option>
          </select>

          {transitionType !== 'cut' && (
            <div className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
              <input
                type="number"
                min="0.1"
                max="3.0"
                step="0.1"
                value={transitionSec}
                onChange={(e) => handleTransitionSecChange(parseFloat(e.target.value) || 0.5)}
                disabled={isBatchRunning}
                className="w-14 bg-[#0b0c10] border border-[#2d313e] rounded px-1.5 py-0.5 text-center text-slate-200 text-[11px] focus:outline-none focus:border-amber-400 font-mono"
              />
              <span>giây</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons for this single scene */}
      <div className="flex items-center gap-2 pt-1 border-t border-[#252834]">
        <button
          onClick={() => onGenerateImage(scene)}
          disabled={scene.imageStatus === 'generating' || isBatchRunning}
          className="flex-1 px-3 py-1.5 bg-[#252a36] hover:bg-[#32394a] disabled:opacity-50 text-slate-200 font-medium rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors"
        >
          <span className="material-symbols-outlined text-[16px] text-amber-400">
            {scene.imageStatus === 'generating' ? 'progress_activity' : 'palette'}
          </span>
          <span>{scene.imageStatus === 'generating' ? 'Đang tạo ảnh...' : 'Tạo ảnh'}</span>
        </button>

        <button
          onClick={() => onGenerateVideo(scene)}
          disabled={
            (!scene.imageBase64 && !scene.imageMediaId) ||
            scene.videoStatus === 'generating' ||
            isBatchRunning
          }
          className="flex-1 px-3 py-1.5 bg-[#1b2533] hover:bg-[#253449] disabled:opacity-40 text-cyan-200 font-medium rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors"
          title={!scene.imageBase64 && !scene.imageMediaId ? 'Cần có ảnh trước khi tạo video' : 'Tạo video từ ảnh này'}
        >
          <span className="material-symbols-outlined text-[16px] text-cyan-400">
            {scene.videoStatus === 'generating' ? 'progress_activity' : 'movie'}
          </span>
          <span>{scene.videoStatus === 'generating' ? 'Đang tạo video...' : 'Tạo video'}</span>
        </button>
      </div>

      {/* Error message banner */}
      {scene.errorMessage && (
        <div className="p-2 rounded bg-rose-950/40 border border-rose-800/40 text-rose-300 text-xs flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[16px]">error</span>
          <span>{scene.errorMessage}</span>
        </div>
      )}
    </div>
  );
};