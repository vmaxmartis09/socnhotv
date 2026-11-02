import React, { useState } from 'react';
import { SceneItem } from '../types';
import { Flow } from 'flow-sdk';

interface ResultSceneTileProps {
  scene: SceneItem;
  clipDuration: number;
}

export const ResultSceneTile: React.FC<ResultSceneTileProps> = ({
  scene,
  clipDuration,
}) => {
  const [downloadState, setDownloadState] = useState<'idle' | 'downloading' | 'done' | 'error'>('idle');

  const formattedIndex = scene.sceneIndex < 10 ? `0${scene.sceneIndex}` : scene.sceneIndex;
  const trans = scene.transition || { type: 'cut', seconds: 0.5 };

  const handleDownloadSingle = async (type: 'image' | 'video') => {
    setDownloadState('downloading');
    try {
      if (type === 'image' && scene.imageBase64) {
        await Flow.download({
          base64: scene.imageBase64,
          mimeType: (scene.imageMimeType as any) || 'image/png',
          filename: `canh_${formattedIndex}.png`,
        });
      } else if (type === 'video' && scene.videoBase64) {
        await Flow.download({
          base64: scene.videoBase64,
          mimeType: (scene.videoMimeType as any) || 'video/mp4',
          filename: `canh_${formattedIndex}.mp4`,
        });
      }
      setDownloadState('done');
      setTimeout(() => setDownloadState('idle'), 2000);
    } catch (e) {
      console.error(e);
      setDownloadState('error');
      setTimeout(() => setDownloadState('idle'), 3000);
    }
  };

  return (
    <div className="bg-[#16181f] border border-[#2a2e3a] rounded-xl overflow-hidden flex flex-col shadow-xl hover:border-amber-500/40 transition-all group">
      {/* Top Banner with Number, Duration & Transition */}
      <div className="bg-[#1d202a] px-3 py-2 border-b border-[#282c38] flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 font-bold">
          <span className="bg-amber-400/20 text-amber-300 border border-amber-400/30 px-1.5 py-0.5 rounded text-[11px] font-mono">
            #{formattedIndex}
          </span>
          <span className="text-slate-200">Cảnh {scene.sceneIndex}</span>
          {scene.locked && (
            <span className="material-symbols-outlined text-[14px] text-amber-400" title="Khóa nguyên văn">
              lock
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className="bg-[#12141a] px-1.5 py-0.5 rounded text-[10px] font-mono text-slate-300 border border-[#2d313d]"
            title={`Chuyển cảnh tiếp: ${trans.type} (${trans.seconds}s)`}
          >
            {trans.type.toUpperCase()}{trans.type !== 'cut' ? ` ${trans.seconds}s` : ''}
          </span>
          <span className="bg-[#12141a] px-2 py-0.5 rounded text-[11px] font-mono text-cyan-300 border border-cyan-500/20">
            {clipDuration}s
          </span>
        </div>
      </div>

      {/* Main Media Preview Display */}
      <div className="relative aspect-video bg-[#0c0d12] overflow-hidden flex items-center justify-center">
        {scene.videoBase64 ? (
          <video
            src={`data:${scene.videoMimeType || 'video/mp4'};base64,${scene.videoBase64}`}
            controls
            playsInline
            loop
            className="w-full h-full object-cover"
          />
        ) : scene.imageBase64 ? (
          <img
            src={`data:${scene.imageMimeType || 'image/png'};base64,${scene.imageBase64}`}
            alt={`Cảnh ${scene.sceneIndex}`}
            className="w-full h-full object-cover"
          />
        ) : scene.imageStatus === 'generating' || scene.videoStatus === 'generating' ? (
          <div className="flex flex-col items-center gap-2 text-amber-400">
            <span className="material-symbols-outlined animate-spin text-[32px]">progress_activity</span>
            <span className="text-xs font-medium">
              {scene.videoStatus === 'generating' ? 'Đang xuất video...' : 'Đang vẽ ảnh...'}
            </span>
          </div>
        ) : (
          <div className="text-center p-4 text-slate-500 flex flex-col items-center gap-1">
            <span className="material-symbols-outlined text-[32px]">movie_edit</span>
            <span className="text-xs">Chưa có kết quả kết xuất</span>
          </div>
        )}

        {/* Media Type Tag */}
        {scene.videoBase64 ? (
          <span className="absolute top-2 left-2 bg-cyan-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 backdrop-blur-sm shadow">
            <span className="material-symbols-outlined text-[12px]">videocam</span>
            <span>VIDEO 3D</span>
          </span>
        ) : scene.imageBase64 ? (
          <span className="absolute top-2 left-2 bg-amber-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 backdrop-blur-sm shadow">
            <span className="material-symbols-outlined text-[12px]">image</span>
            <span>KHUNG ẢNH ĐẦU</span>
          </span>
        ) : null}
      </div>

      {/* Prompts Preview & Download Controls */}
      <div className="p-3 flex-1 flex flex-col justify-between gap-3 text-xs">
        <div className="space-y-1.5">
          <p className="text-slate-300 font-medium line-clamp-2" title={scene.videoPrompt}>
            <span className="text-slate-400 font-semibold mr-1">Diễn xuất:</span>
            {scene.videoPrompt}
          </p>
          <p className="text-slate-400 text-[11px] line-clamp-1 italic" title={scene.imagePrompt}>
            <span className="text-slate-500 font-semibold mr-1">Bối cảnh:</span>
            {scene.imagePrompt}
          </p>
        </div>

        {/* Footer with Individual Download Buttons */}
        <div className="pt-2 border-t border-[#252834] flex items-center justify-between gap-2">
          <div className="flex items-center gap-1">
            {scene.imageBase64 && (
              <button
                onClick={() => handleDownloadSingle('image')}
                disabled={downloadState === 'downloading'}
                className="px-2 py-1 bg-[#222632] hover:bg-[#2e3444] text-slate-300 rounded text-[11px] flex items-center gap-1 transition-colors"
                title="Tải ảnh cảnh này"
              >
                <span className="material-symbols-outlined text-[13px]">image</span>
                <span>Tải ảnh</span>
              </button>
            )}
            {scene.videoBase64 && (
              <button
                onClick={() => handleDownloadSingle('video')}
                disabled={downloadState === 'downloading'}
                className="px-2 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800/40 rounded text-[11px] flex items-center gap-1 transition-colors"
                title="Tải video cảnh này"
              >
                <span className="material-symbols-outlined text-[13px]">download</span>
                <span>Tải MP4</span>
              </button>
            )}
          </div>

          {downloadState === 'done' && (
            <span className="text-emerald-400 text-[11px] flex items-center gap-0.5">
              <span className="material-symbols-outlined text-[14px]">check</span>
              <span>Đã tải!</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};