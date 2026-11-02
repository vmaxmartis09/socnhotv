import React, { useState } from 'react';
import { Character } from '../types';
import { Flow } from 'flow-sdk';

interface CharacterCardProps {
  char: Character;
  styleBible: string;
  selectedImageModel: string;
  onUpdate: (updated: Character) => void;
  onDelete: (id: string) => void;
}

export const CharacterCard: React.FC<CharacterCardProps> = ({
  char,
  styleBible,
  selectedImageModel,
  onUpdate,
  onDelete,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(char.name);
  const [desc, setDesc] = useState(char.description);
  const [prompt, setPrompt] = useState(char.prompt);
  const [isSelectingProject, setIsSelectingProject] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleGenerate = async () => {
    onUpdate({ ...char, status: 'generating', errorMessage: undefined });
    try {
      // Rule: Full body, front facing, pure white background, no text
      const cleanStyle = styleBible.trim();
      const characterPrompt = `${prompt.trim()}, ${desc.trim()}, nhân vật hoạt hình 3D đứng chính diện toàn thân, toàn bộ cơ thể từ đầu đến chân hiển thị rõ, trên nền trắng tinh khiết thuần nhất không vật cản (pure solid white background, full body centered front view, character turnaround reference sheet style), không logo, không chữ, không phụ đề${cleanStyle ? `, ${cleanStyle}` : ''}`;

      const res = await Flow.generate.image({
        prompt: characterPrompt,
        modelDisplayName: selectedImageModel,
        aspectRatio: '1:1',
      });

      onUpdate({
        ...char,
        name,
        description: desc,
        prompt,
        status: 'ready',
        mediaId: res.mediaId,
        base64: res.base64,
        mimeType: res.mimeType,
      });
    } catch (err) {
      onUpdate({
        ...char,
        status: 'error',
        errorMessage: err instanceof Error ? err.message : 'Tạo ảnh thất bại',
      });
    }
  };

  // Mục 1: Chọn nhân vật từ kho nhân vật / thư viện của Flow (giữ nguyên tên và mô tả đã nhập, dùng làm ảnh tham chiếu, không tạo ảnh mới)
  const handleSelectFromFlowLibrary = async () => {
    setIsSelectingProject(true);
    try {
      // Dùng Flow media picker cho image
      const selected = await Flow.media.select({ filter: 'image' });
      onUpdate({
        ...char,
        name: char.name, // Giữ nguyên tên đã nhập
        description: char.description, // Giữ nguyên mô tả đã nhập
        status: 'ready',
        mediaId: selected.mediaId,
        base64: selected.base64,
        mimeType: selected.mimeType,
        errorMessage: undefined,
      });
    } catch (err) {
      console.warn('Selection from Flow library canceled or failed', err);
    } finally {
      setIsSelectingProject(false);
    }
  };

  const handleUploadExisting = async () => {
    setIsUploading(true);
    try {
      const selected = await Flow.media.select({ filter: 'image' });
      onUpdate({
        ...char,
        status: 'ready',
        mediaId: selected.mediaId,
        base64: selected.base64,
        mimeType: selected.mimeType,
        errorMessage: undefined,
      });
    } catch (err) {
      console.warn('Selection canceled or failed', err);
    } finally {
      setIsUploading(false);
    }
  };

  const saveEdits = () => {
    onUpdate({
      ...char,
      name,
      description: desc,
      prompt,
    });
    setIsEditing(false);
  };

  return (
    <div className="bg-[#181a20] border border-[#2e323b] rounded-xl p-4 transition-all hover:border-[#424856] shadow-lg flex flex-col gap-3">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-amber-400 text-[20px]">cruelty_free</span>
          <span className="font-bold text-slate-100 text-sm">{char.name || 'Chưa đặt tên'}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-[#252830] transition-colors"
            title="Sửa thông tin"
          >
            <span className="material-symbols-outlined text-[18px]">
              {isEditing ? 'close' : 'edit'}
            </span>
          </button>
          <button
            onClick={() => onDelete(char.id)}
            className="p-1.5 text-rose-400 hover:text-rose-300 rounded-lg hover:bg-rose-950/30 transition-colors"
            title="Xóa nhân vật"
          >
            <span className="material-symbols-outlined text-[18px]">delete</span>
          </button>
        </div>
      </div>

      {/* Preview and quick info */}
      <div className="flex gap-3">
        {/* Character Image Thumbnail */}
        <div className="w-24 h-24 rounded-lg bg-[#0e1015] border border-[#2b2e38] flex items-center justify-center shrink-0 overflow-hidden relative group">
          {char.base64 ? (
            <img
              src={`data:${char.mimeType || 'image/png'};base64,${char.base64}`}
              alt={char.name}
              className="w-full h-full object-contain bg-white"
            />
          ) : char.status === 'generating' ? (
            <div className="flex flex-col items-center gap-1 text-amber-400">
              <span className="material-symbols-outlined animate-spin text-[24px]">progress_activity</span>
              <span className="text-[10px]">Đang tạo...</span>
            </div>
          ) : (
            <div className="text-center p-1 text-slate-500 flex flex-col items-center">
              <span className="material-symbols-outlined text-[24px]">person</span>
              <span className="text-[10px]">Chưa có ảnh</span>
            </div>
          )}

          {char.status === 'ready' && (
            <div className="absolute top-1 right-1 bg-emerald-500/90 text-white rounded-full p-0.5 shadow">
              <span className="material-symbols-outlined text-[12px] block">check</span>
            </div>
          )}
        </div>

        {/* Info or Edit Fields */}
        <div className="flex-1 min-w-0 flex flex-col justify-between text-xs">
          {isEditing ? (
            <div className="flex flex-col gap-2">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Tên nhân vật..."
                className="bg-[#0f1117] border border-[#2b2f3a] rounded px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
              />
              <textarea
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                rows={2}
                placeholder="Mô tả cố định (vài câu)..."
                className="bg-[#0f1117] border border-[#2b2f3a] rounded px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-amber-500 resize-none"
              />
              <button
                onClick={saveEdits}
                className="self-start px-2.5 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded text-[11px] transition-colors"
              >
                Lưu sửa
              </button>
            </div>
          ) : (
            <div className="space-y-1">
              <p className="text-slate-300 line-clamp-2 italic font-serif">
                "{char.description || 'Chưa có mô tả ngoại hình'}"
              </p>
              <p className="text-[11px] text-slate-500 line-clamp-1 font-mono">
                Prompt: {char.prompt}
              </p>
            </div>
          )}

          {/* Action Row */}
          <div className="flex flex-wrap items-center gap-1.5 mt-2 pt-2 border-t border-[#262a34]">
            {/* Nút 1: Chọn từ kho nhân vật của Flow */}
            <button
              onClick={handleSelectFromFlowLibrary}
              disabled={isSelectingProject}
              className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded flex items-center gap-1 text-[11px] font-medium transition-colors"
              title="Chọn ảnh từ kho dự án Flow làm ảnh tham chiếu trực tiếp"
            >
              <span className="material-symbols-outlined text-[14px]">account_box</span>
              <span>{isSelectingProject ? 'Đang mở...' : 'Chọn từ kho nhân vật'}</span>
            </button>

            <button
              onClick={handleGenerate}
              disabled={char.status === 'generating'}
              className="px-2.5 py-1 bg-[#282d38] hover:bg-[#343b4a] disabled:opacity-50 text-slate-200 font-medium rounded flex items-center gap-1 text-[11px] transition-colors"
            >
              <span className="material-symbols-outlined text-[14px] text-amber-400">
                {char.status === 'generating' ? 'hourglass_top' : 'auto_fix_high'}
              </span>
              <span>{char.status === 'generating' ? 'Đang tạo...' : 'Tạo ảnh'}</span>
            </button>

            <button
              onClick={handleUploadExisting}
              disabled={isUploading}
              className="px-2.5 py-1 bg-[#1f232b] hover:bg-[#2b313d] text-slate-300 rounded flex items-center gap-1 text-[11px] transition-colors"
            >
              <span className="material-symbols-outlined text-[14px]">upload_file</span>
              <span>Tải ảnh lên</span>
            </button>
          </div>
        </div>
      </div>

      {/* Prompt input if needing quick tweak */}
      {!isEditing && (
        <div className="mt-1">
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-1">
            Prompt ảnh tham chiếu (toàn thân, nền trắng)
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={char.prompt}
              onChange={(e) => onUpdate({ ...char, prompt: e.target.value })}
              placeholder="Ví dụ: chú sóc nhỏ mặc áo len đỏ, đôi mắt to tròn lấp lánh..."
              className="flex-1 bg-[#0e1015] border border-[#2b2e38] rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
            />
          </div>
        </div>
      )}

      {/* Error display */}
      {char.errorMessage && (
        <div className="p-2 rounded bg-rose-950/40 border border-rose-800/40 text-rose-300 text-[11px] flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[14px]">error</span>
          <span>{char.errorMessage}</span>
        </div>
      )}
    </div>
  );
};