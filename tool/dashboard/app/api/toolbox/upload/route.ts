import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import crypto from "crypto";
import { INBOX_DIR, safeName } from "@/lib/toolbox-paths";

const MAX_BYTES = 200 * 1024 * 1024;
const ALLOWED = new Set([".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".webm"]);

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const file = form.get("file");
    if (!(file instanceof File)) return NextResponse.json({ ok: false, error: "Thiếu file" }, { status: 400 });
    const ext = path.extname(file.name).toLowerCase();
    if (!ALLOWED.has(ext)) {
      return NextResponse.json({ ok: false, error: `Định dạng ${ext || "?"} không được hỗ trợ` }, { status: 415 });
    }
    if (file.size > MAX_BYTES) return NextResponse.json({ ok: false, error: "File quá lớn (>200MB)" }, { status: 413 });

    const buf = Buffer.from(await file.arrayBuffer());
    const sha = crypto.createHash("sha256").update(buf).digest("hex").slice(0, 8);
    fs.mkdirSync(INBOX_DIR, { recursive: true });
    const dest = path.join(INBOX_DIR, `${sha}_${safeName(file.name)}`);
    if (!fs.existsSync(dest)) {
      const tmp = dest + ".tmp";
      fs.writeFileSync(tmp, buf);
      fs.renameSync(tmp, dest);
    }
    return NextResponse.json({ ok: true, path: dest, name: file.name, size: buf.length });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}
