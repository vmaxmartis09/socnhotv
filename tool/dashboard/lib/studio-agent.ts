import { getRepository } from "@/lib/repositories";
import { checkCoreHealth, validateGraphWithCore } from "@/lib/core-api";
import { fetchProjectLibrary, createProject } from "@/lib/repositories/library";
import { generateCharacterDraft } from "@/lib/repositories/character-assets";
import { confirm } from "@/lib/confirm";
import { useStudioStore } from "@/store";
import type { Character } from "@/lib/repositories";

/**
 * Trợ lý Chat cục bộ: hiểu lệnh tiếng Việt/Anh để tạo hoặc kiểm tra mọi thứ trong dự án.
 * Trả về chuỗi trả lời nếu đã xử lý, hoặc null để chuyển cho trợ lý Core/Gemini.
 * Mọi thao tác tạo/xóa đều qua hộp xác nhận chung.
 */
export async function runLocalAgent(
  prompt: string,
  nav: { push: (path: string) => void }
): Promise<string | null> {
  const p = prompt.trim();
  const low = p.toLowerCase();
  const st = () => useStudioStore.getState();
  const pid = st().activeProjectId;
  const after = (re: RegExp) => p.replace(re, "").replace(/^[\s:,\-–]+/, "").trim();

  // ---------- Tạo ----------
  if (/^(tạo|thêm|create|add)\s+(một\s+)?(nhân vật|character)/i.test(p)) {
    const desc = after(/^(tạo|thêm|create|add)\s+(một\s+)?(nhân vật|character)/i);
    if (!desc) return "Hãy mô tả nhân vật, ví dụ: “tạo nhân vật bác sĩ cú mèo tên Cú Mèo, 140cm, hiền và thông minh”.";
    const { draft, mode } = await generateCharacterDraft(pid, desc, st().isMockMode);
    const ok = await confirm({
      tone: "info",
      title: `Tạo nhân vật “${draft.name}”?`,
      message: `${draft.role === "main" ? "Chính" : "Phụ"} · ${draft.heightCm} cm · ${draft.personality}. (${mode === "gemini" ? "Gemini" : "bản nháp theo quy tắc"})`,
    });
    if (!ok) return "Đã hủy, chưa tạo nhân vật nào.";
    const id = draft.name.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || `char_${Date.now().toString(36)}`;
    const c: Character = {
      id,
      projectId: pid,
      name: draft.name,
      role: draft.role,
      heightCm: draft.heightCm,
      scaleRatio: Math.round((draft.heightCm / 100) * 100) / 100,
      voiceId: "",
      description: draft.description,
      promptLock: draft.promptLock,
      referenceImages: [],
      memory: { personality: draft.personality, catchphrases: draft.catchphrases ?? [], habits: draft.habits ?? [], pastEventsSummary: [] },
    };
    await getRepository().createCharacter(c);
    st().setCharacters(await getRepository().listCharacters(pid));
    return `Đã tạo nhân vật “${draft.name}” (${draft.heightCm} cm). Mở panel Nhân vật để thêm ảnh và giọng.`;
  }

  if (/^(tạo|thêm|create|add)\s+(một\s+)?(tập|episode)/i.test(p)) {
    const title = after(/^(tạo|thêm|create|add)\s+(một\s+)?(tập|episode)(\s+phim)?/i) || "Câu chuyện mới";
    if (!(await confirm({ tone: "info", title: `Tạo tập “${title}”?`, message: `Trong dự án ${pid}` }))) return "Đã hủy.";
    const ep = st().createEpisode(title);
    return `Đã tạo “${ep.title}” và chuyển canvas sang tập này.`;
  }

  if (/^(tạo|create)\s+(một\s+)?(dự án|project)/i.test(p)) {
    const name = after(/^(tạo|create)\s+(một\s+)?(dự án|project)/i);
    const id = name.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    if (!id) return "Hãy đặt tên dự án, ví dụ: “tạo dự án Khu Rừng Kỳ Diệu”.";
    if (!(await confirm({ tone: "info", title: `Tạo dự án “${name}”?`, message: `Mã dự án: ${id}` }))) return "Đã hủy.";
    await createProject({ id, name });
    st().setProjects(await getRepository().listProjects());
    st().switchProject(id);
    nav.push("/studio");
    return `Đã tạo dự án “${name}” và chuyển vào Studio.`;
  }

  // ---------- Điều hướng ----------
  if (/^(mở|đi tới|open|go to)\s+(sảnh|home)/i.test(p)) {
    nav.push("/");
    return "Đã về Sảnh.";
  }
  if (/^(mở|đi tới|open|go to)\s+(công việc|jobs|tiến trình)/i.test(p)) {
    nav.push("/jobs");
    return "Đã mở trang Công việc.";
  }

  // ---------- Kiểm tra ----------
  if (/(core|health|hệ thống|sức khỏe)/.test(low) && /(kiểm tra|check|trạng thái|status)/.test(low)) {
    const h = await checkCoreHealth();
    return h.online ? `Core đang chạy (v${h.version}).` : "Core không phản hồi. Bật bằng: uvicorn socnhotv.core.api.app:app --app-dir src --port 8000";
  }
  if (/(đồ thị|graph|canvas)/.test(low) && /(kiểm tra|validate|check)/.test(low)) {
    const s = st();
    try {
      const { toCoreGraph } = await import("@/components/canvas/StudioCanvas");
      const res = await validateGraphWithCore(pid, toCoreGraph(pid, s.nodes, s.edges), s.nodeCatalog);
      return res.isValid
        ? `Đồ thị hợp lệ (${res.topologicalOrder.length} bước)${res.warnings.length ? `, ${res.warnings.length} cảnh báo` : ""}.`
        : `Đồ thị có ${res.errors.length} lỗi: ${res.errors.slice(0, 3).join("; ")}`;
    } catch {
      return "Không kiểm tra được đồ thị lúc này (Core không phản hồi).";
    }
  }
  if (/(tiến trình|đang chạy|jobs|hàng đợi|queue)/.test(low)) {
    const jobs = st().jobs;
    const live = jobs.filter((j) => j.status === "running" || j.status === "queued");
    return live.length
      ? `Đang chạy ${live.length} tiến trình: ${live.slice(0, 4).map((j) => `${j.type}${j.nodeId ? ` (${j.nodeId})` : ""} ${Math.round(j.progress)}%`).join(", ")}.`
      : `Không có tiến trình nào đang chạy. Tổng ${jobs.length} công việc đã ghi nhận.`;
  }
  if (/(chi phí|spend|ngân sách|budget)/.test(low)) {
    const s = st();
    return `Đã chi $${s.totalSpentUsd.toFixed(2)} / trần ngày $${s.dailySpendingLimitUsd}. Mỗi lần chạy tối đa $${s.perRunSpendingLimitUsd}. Chế độ: ${s.isMockMode ? "chạy thử ($0)" : "API thật"}.`;
  }
  if (/(dự án|projects)/.test(low) && /(danh sách|liệt kê|list|có những|mấy|bao nhiêu)/.test(low)) {
    return st().projects.map((x) => `• ${x.name} (${x.charactersCount} nhân vật, ${x.episodesCount} tập)`).join("\n") || "Chưa có dự án nào.";
  }
  if (/(nhân vật|characters)/.test(low) && /(danh sách|liệt kê|list|có những|mấy|bao nhiêu|xem)/.test(low)) {
    const cs = st().characters;
    return cs.length ? cs.map((c) => `• ${c.name} — ${c.heightCm} cm, giọng ${c.voiceId || "—"}, ${c.referenceImages.length} ảnh`).join("\n") : "Dự án này chưa có nhân vật.";
  }
  if (/(tập|episodes)/.test(low) && /(danh sách|liệt kê|list|có những|mấy|bao nhiêu)/.test(low)) {
    return st().episodes.map((e) => `• ${e.title} (${e.status})`).join("\n");
  }
  if (/(kho|library|video|hình ảnh|ảnh|kịch bản)/.test(low) && /(bao nhiêu|mấy|đếm|kiểm tra|count|có)/.test(low)) {
    try {
      const l = await fetchProjectLibrary(pid);
      return `Kho tư liệu: ${l.videos.length} video, ${l.images.length} hình ảnh, ${l.scripts.length} kịch bản, ${l.episodes.length} tập.`;
    } catch {
      return "Không đọc được kho tư liệu (Core không phản hồi).";
    }
  }

  return null;
}
