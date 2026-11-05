import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { DATA_DIR, isInside } from "@/lib/toolbox-paths";

const TYPES: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
  ".m4a": "audio/mp4",
  ".ogg": "audio/ogg",
  ".flac": "audio/flac",
  ".mp4": "video/mp4",
  ".webm": "video/webm",
  ".srt": "text/plain; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const filePath = searchParams.get("path");
  if (!filePath) return new NextResponse("Missing file path", { status: 400 });

  const resolved = path.resolve(filePath);
  // Chỉ phục vụ file trong data/ (trước đây đọc được mọi đường dẫn trên máy)
  if (!isInside(DATA_DIR, resolved)) return new NextResponse("Forbidden", { status: 403 });
  const ext = path.extname(resolved).toLowerCase();
  if (!TYPES[ext]) return new NextResponse("Unsupported type", { status: 415 });
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) return new NextResponse("File not found", { status: 404 });

  const buf = fs.readFileSync(resolved);
  const headers: Record<string, string> = { "Content-Type": TYPES[ext], "Cache-Control": "no-store" };
  if (searchParams.get("download")) headers["Content-Disposition"] = `attachment; filename="${path.basename(resolved)}"`;
  return new NextResponse(buf, { headers });
}
