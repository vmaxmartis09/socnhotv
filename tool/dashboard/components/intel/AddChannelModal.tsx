"use client";

import React, { useState } from "react";
import { intelApi, ChannelAnalysisResponse } from "@/lib/api/intel";
import { Tv, Sparkles, ExternalLink } from "./icons";
import { X, Loader2 } from "@/components/ui/icons";

interface AddChannelModalProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
  onSuccess: (res: ChannelAnalysisResponse) => void;
}

export function AddChannelModal({
  isOpen,
  projectId,
  onClose,
  onSuccess,
}: AddChannelModalProps) {
  const [url, setUrl] = useState("");
  const [maxVideos, setMaxVideos] = useState(50);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      const res = await intelApi.ingestChannel(projectId, url.trim(), maxVideos);
      onSuccess(res);
      onClose();
    } catch (err: any) {
      setError(`Lỗi phân tích kênh: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Tv className="h-5 w-5 text-indigo-400" />
            <h2 className="text-base font-bold text-zinc-100">Học Kênh Đối Thủ Mới</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-lg border border-rose-900/50 bg-rose-950/30 p-2.5 text-xs text-rose-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="text-xs font-semibold text-zinc-300">
              Liên kết Kênh YouTube / TikTok / Douyin
            </label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/@ChannelName hoặc TikTok"
              className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
            />
            <p className="mt-1 text-[11px] text-zinc-500">
              Hệ thống dùng <code className="text-indigo-400 font-mono">yt-dlp extract_flat</code> lấy metadata nhanh chóng không tải hàng loạt video.
            </p>
          </div>

          <div>
            <label className="text-xs font-semibold text-zinc-300">
              Số lượng video mới nhất cần quét (N)
            </label>
            <input
              type="number"
              min={10}
              max={200}
              value={maxVideos}
              onChange={(e) => setMaxVideos(Number(e.target.value))}
              className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-zinc-100 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="mt-6 flex items-center justify-end gap-2 pt-3 border-t border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-zinc-700 px-3.5 py-2 text-xs font-semibold text-zinc-300 hover:bg-zinc-800"
            >
              Huỷ
            </button>
            <button
              type="submit"
              disabled={isLoading || !url.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
            >
              {isLoading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Sparkles className="h-3.5 w-3.5" />
              )}
              Bắt đầu phân tích
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
