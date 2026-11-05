import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// Xác định đường dẫn gốc repo linh hoạt theo môi trường thực thi Next.js
function getRepoRoot(): string {
  const cwd = process.cwd();
  if (fs.existsSync(path.join(cwd, "data", "shared", "templates"))) {
    return cwd;
  }
  const parent2 = path.resolve(cwd, "../..");
  if (fs.existsSync(path.join(parent2, "data", "shared", "templates"))) {
    return parent2;
  }
  const parent1 = path.resolve(cwd, "..");
  if (fs.existsSync(path.join(parent1, "data", "shared", "templates"))) {
    return parent1;
  }
  return cwd;
}

const REPO_ROOT = getRepoRoot();
const TEMPLATES_ROOT = path.join(REPO_ROOT, "data", "shared", "templates");
const TOOLS_ROOT = path.join(REPO_ROOT, "tool", "toolbox", "tools");

// Đọc danh sách khóa API từ .env hoặc .env.local nếu có
function getAvailableApiKeys(): Set<string> {
  const keys = new Set<string>();
  // 1. process.env
  for (const [k, v] of Object.entries(process.env)) {
    if (v && v.trim().length > 10 && !v.toLowerCase().includes("placeholder")) {
      keys.add(k.toUpperCase());
    }
  }
  // 2. Tệp .env và .env.local
  for (const envName of [".env.local", ".env"]) {
    const envPath = path.join(REPO_ROOT, envName);
    if (fs.existsSync(envPath)) {
      try {
        const content = fs.readFileSync(envPath, "utf-8");
        for (const line of content.split("\n")) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
          const [k, ...rest] = trimmed.split("=");
          const val = rest.join("=").trim().replace(/^['"]|['"]$/g, "");
          if (val.length > 10 && !val.toLowerCase().includes("placeholder")) {
            keys.add(k.trim().toUpperCase());
          }
        }
      } catch {}
    }
  }
  return keys;
}

// Kiểm tra tool đã được cài đặt và verified trong Toolbox chưa
function getInstalledTools(): Set<string> {
  const installed = new Set<string>();
  if (fs.existsSync(TOOLS_ROOT)) {
    const dirs = fs.readdirSync(TOOLS_ROOT);
    for (const d of dirs) {
      const manifestPath = path.join(TOOLS_ROOT, d, "tool.json");
      if (fs.existsSync(manifestPath)) {
        try {
          const t = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
          if (t.id) {
            installed.add(t.id);
          }
        } catch {}
      }
    }
  }
  return installed;
}

// Kiểm tra máy chủ có GPU NVIDIA không (hiện máy chỉ có CPU)
function hasNvidiaGpu(): boolean {
  return false;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const categoryFilter = searchParams.get("category");
    const kindFilter = searchParams.get("kind");
    const tierFilter = searchParams.get("tier");
    const idFilter = searchParams.get("id");

    if (!fs.existsSync(TEMPLATES_ROOT)) {
      return NextResponse.json(
        { ok: false, error: "Thư mục templates không tồn tại", templates: [] },
        { status: 500 }
      );
    }

    const availableKeys = getAvailableApiKeys();
    const installedTools = getInstalledTools();
    const gpuAvailable = hasNvidiaGpu();

    const templateDirs = fs.readdirSync(TEMPLATES_ROOT).filter((name) => {
      if (name.startsWith("_") || name.startsWith(".")) return false;
      const fullPath = path.join(TEMPLATES_ROOT, name);
      return fs.statSync(fullPath).isDirectory();
    });

    const templates: any[] = [];

    for (const dirName of templateDirs) {
      const jsonPath = path.join(TEMPLATES_ROOT, dirName, "template.json");
      if (!fs.existsSync(jsonPath)) continue;

      try {
        const raw = fs.readFileSync(jsonPath, "utf-8");
        const t = JSON.parse(raw);

        // Áp dụng bộ lọc
        if (idFilter && t.id !== idFilter) continue;
        if (categoryFilter && t.category !== categoryFilter) continue;
        if (kindFilter && t.kind !== kindFilter) continue;
        if (tierFilter && t.tier !== tierFilter) continue;

        // Kiểm tra điều kiện khả dụng
        const missingRequirements: string[] = [];

        // 1. Kiểm tra Tools
        const reqTools = t.requires?.tools || [];
        for (const toolId of reqTools) {
          if (!installedTools.has(toolId)) {
            missingRequirements.push(`Toolbox thiếu công cụ: '${toolId}'`);
          }
        }

        // 2. Kiểm tra Providers
        const reqProviders = t.requires?.providers || [];
        for (const prov of reqProviders) {
          const provLower = prov.toLowerCase();
          const matchedKey =
            provLower === "gemini" || provLower === "google"
              ? availableKeys.has("GEMINI_API_KEY") || availableKeys.has("GOOGLE_API_KEY")
              : provLower === "claude" || provLower === "anthropic"
              ? availableKeys.has("ANTHROPIC_API_KEY")
              : provLower === "openai"
              ? availableKeys.has("OPENAI_API_KEY")
              : provLower === "fal"
              ? availableKeys.has("FAL_KEY")
              : availableKeys.has(`${prov.toUpperCase()}_API_KEY`);

          if (!matchedKey) {
            missingRequirements.push(
              `Thiếu khóa API nhà cung cấp '${prov}' (cấu hình trong Cài đặt hoặc .env)`
            );
          }
        }

        // 3. Kiểm tra GPU
        if (t.requires?.gpu && !gpuAvailable) {
          missingRequirements.push(
            "Yêu cầu GPU NVIDIA phần cứng (máy hiện tại chỉ có CPU; cần dùng Tier A thay thế)"
          );
        }

        const isAvailable = missingRequirements.length === 0;

        templates.push({
          ...t,
          is_available: isAvailable,
          missing_requirements: missingRequirements,
          preview_mp4_url: `/core/video/templates/${t.id}/preview.mp4`,
          preview_jpg_url: `/core/video/templates/${t.id}/preview.jpg`,
        });
      } catch (err) {
        console.error(`Lỗi đọc template ${dirName}:`, err);
      }
    }

    // Nếu hỏi 1 ID duy nhất
    if (idFilter) {
      if (templates.length === 0) {
        return NextResponse.json(
          { ok: false, error: `Không tìm thấy template '${idFilter}'` },
          { status: 404 }
        );
      }
      return NextResponse.json({ ok: true, template: templates[0] });
    }

    return NextResponse.json({
      ok: true,
      total: templates.length,
      templates,
    });
  } catch (err: any) {
    return NextResponse.json(
      { ok: false, error: err.message || "Lỗi máy chủ nội bộ" },
      { status: 500 }
    );
  }
}
