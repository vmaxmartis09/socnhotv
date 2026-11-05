import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { DATA_DIR, SHARED_DIR, isInside, safeName, readProjects, readCharacters } from "@/lib/toolbox-paths";

/**
 * Lưu file từ kho Toolbox vào dự án hoặc nhân vật (CHỈ sao chép, không ghi đè file có sẵn).
 *  - project   → data/projects/<pid>/library/toolbox/
 *  - character → data/projects/<pid>/characters/<cid>/toolbox/
 */
export async function POST(request: Request) {
  try {
    const { src, projectId, characterId, name } = await request.json();
    if (!src || !projectId) return NextResponse.json({ ok: false, error: "Thiếu src hoặc projectId" }, { status: 400 });

    const resolved = path.resolve(String(src));
    if (!isInside(SHARED_DIR, resolved) || !fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) {
      return NextResponse.json({ ok: false, error: "Nguồn không hợp lệ (phải nằm trong kho dùng chung)" }, { status: 400 });
    }
    if (!readProjects().some((p) => p.id === projectId)) {
      return NextResponse.json({ ok: false, error: "Dự án không tồn tại" }, { status: 404 });
    }
    let destDir = path.join(DATA_DIR, "projects", projectId, "library", "toolbox");
    if (characterId) {
      if (!readCharacters(projectId).some((c) => c.id === characterId)) {
        return NextResponse.json({ ok: false, error: "Nhân vật không tồn tại trong dự án" }, { status: 404 });
      }
      destDir = path.join(DATA_DIR, "projects", projectId, "characters", characterId, "toolbox");
    }
    fs.mkdirSync(destDir, { recursive: true });

    const ext = path.extname(resolved);
    // File trong kho (assets/<loại>/<mã>/cutout.png) → đặt tên "<mã>_cutout.png" cho dễ nhận ra
    const parent = path.basename(path.dirname(resolved));
    const inVault = /^[0-9a-f]{8}$/i.test(parent);
    const given = name ? safeName(String(name)) : inVault ? `${parent}_${path.basename(resolved)}` : path.basename(resolved);
    const stem = given.toLowerCase().endsWith(ext.toLowerCase()) ? given.slice(0, given.length - ext.length) : given;
    let dest = path.join(destDir, `${stem}${ext}`);
    for (let i = 2; fs.existsSync(dest); i++) dest = path.join(destDir, `${stem}_${i}${ext}`);
    fs.copyFileSync(resolved, dest, fs.constants.COPYFILE_EXCL);

    return NextResponse.json({ ok: true, savedTo: dest, relative: path.relative(DATA_DIR, dest).replace(/\\/g, "/") });
  } catch (err: any) {
    return NextResponse.json({ ok: false, error: err.message }, { status: 500 });
  }
}
