"use client";

import React, { useEffect, useRef, useState } from "react";
import { useStudioStore } from "@/store";
import {
  checkPolicyText,
  fetchPolicyPacks,
  fetchPolicyUrl,
  fetchProjectPolicy,
  importPolicyFile,
  importPolicyPack,
  saveProjectPolicy,
  type ContentPolicy,
  type PolicyPack,
  type PolicyReport,
  type PolicyRule,
} from "@/lib/api/policy";
import { Download, ExternalLink, Plus, ShieldCheck, Trash2, Upload } from "@/components/ui/icons";
import { Reveal } from "@/components/canvas/Reveal";
import { cn } from "@/lib/utils";

const field =
  "rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand";

const SCOPE_LABEL: Record<string, string> = {
  dialogue: "Lời thoại",
  caption: "Caption",
  script: "Kịch bản",
  prompt: "Prompt ảnh/video",
};

/** Chính sách nội dung xuyên suốt dự án: từ ngữ cấm theo nhóm, mức độ, phạm vi kiểm. */
export function PolicyEditor({ projectId: projectIdProp }: { projectId?: string } = {}) {
  const activeId = useStudioStore((s: any) => s.activeProjectId) as string;
  // Chính sách thuộc về TỪNG dự án: dùng dự án được truyền vào (hub đang xem), mặc định là dự án đang mở
  const projectId = projectIdProp || activeId;
  const [policy, setPolicy] = useState<ContentPolicy | null>(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [sample, setSample] = useState("");
  const [report, setReport] = useState<PolicyReport | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [packs, setPacks] = useState<PolicyPack[]>([]);
  const [srcOpen, setSrcOpen] = useState(false);
  const [srcBusy, setSrcBusy] = useState<string | null>(null);
  const [srcMsg, setSrcMsg] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [page, setPage] = useState<{ title: string; chars: number; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    fetchPolicyPacks().then(setPacks);
  }, []);

  useEffect(() => {
    let alive = true;
    setPolicy(null);
    fetchProjectPolicy(projectId).then((p) => {
      if (alive) {
        setPolicy(p);
        setDirty(false);
      }
    });
    return () => {
      alive = false;
    };
  }, [projectId]);

  if (!policy)
    return <p className="text-[13px] text-muted-foreground">Chưa đọc được chính sách (core chưa chạy?).</p>;

  const patch = (p: Partial<ContentPolicy>) => {
    setPolicy({ ...policy, ...p });
    setDirty(true);
    setMsg(null);
  };
  const patchRule = (id: string, p: Partial<PolicyRule>) =>
    patch({ rules: policy.rules.map((r) => (r.id === id ? { ...r, ...p } : r)) });
  const addRule = () => {
    const id = `rule_${Date.now().toString(36)}`;
    patch({
      rules: [...policy.rules, { id, category: "Mới", label: "Quy tắc mới", severity: "block", enabled: true, terms: [] }],
    });
    setOpen(id);
  };

  const save = async () => {
    setBusy(true);
    try {
      setPolicy(await saveProjectPolicy(projectId, policy));
      setDirty(false);
      setMsg("Đã lưu chính sách cho cả dự án.");
    } catch (e: any) {
      setMsg(e?.message || "Lưu thất bại");
    } finally {
      setBusy(false);
    }
  };

  // Các thao tác nhập đều lưu thẳng vào chính sách của dự án rồi nạp lại
  const runSource = async (key: string, fn: () => Promise<string>) => {
    setSrcBusy(key);
    setSrcMsg(null);
    try {
      setSrcMsg(await fn());
      setDirty(false);
    } catch (e: any) {
      setSrcMsg(e?.message || "Thao tác thất bại");
    } finally {
      setSrcBusy(null);
    }
  };
  const addPack = (pk: PolicyPack) =>
    runSource(pk.id, async () => {
      setPolicy(await importPolicyPack(projectId, pk.id));
      return `Đã thêm gói "${pk.name}" (${pk.ruleCount} quy tắc).`;
    });
  const onFile = (f: File) =>
    runSource("file", async () => {
      const r = await importPolicyFile(projectId, f.name, await f.text());
      setPolicy(r.policy);
      return `Đã nhập ${r.added} nhóm / ${r.terms} từ từ "${f.name}".`;
    });
  const onUrl = () =>
    runSource("url", async () => {
      const r = await fetchPolicyUrl(projectId, url.trim());
      setPolicy(r.policy);
      setPage(r.page);
      return `Đã lấy "${r.page.title}" (${r.page.chars.toLocaleString("vi-VN")} ký tự) làm tài liệu tham chiếu. Thêm từ cấm vào quy tắc dựa trên nội dung này.`;
    });
  const exportPolicy = () => {
    const blob = new Blob([JSON.stringify(policy, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `policy-${projectId}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const test = async () => setReport(await checkPolicyText(projectId, { "văn bản thử": sample }));

  return (
    <div className="space-y-3">
      <label className="block space-y-1">
        <span className="text-muted-foreground">Tên chính sách</span>
        <input
          value={policy.name}
          onChange={(e) => patch({ name: e.target.value })}
          className={cn(field, "h-8 w-full")}
        />
      </label>

      <div className="space-y-1.5 rounded-md border border-border p-2">
        <button
          type="button"
          onClick={() => setSrcOpen((v) => !v)}
          className="flex w-full items-center justify-between text-left text-xs text-foreground"
        >
          <span className="font-medium">Nguồn chính sách chuẩn</span>
          <span className="text-muted-foreground">{srcOpen ? "Thu gọn" : "Gói nền tảng · Tải lên · Từ URL"}</span>
        </button>
        <Reveal show={srcOpen}>
          <div className="space-y-3 pt-1.5">
            <div className="space-y-1">
              <span className="text-[13px] text-muted-foreground">Gói chuẩn của nền tảng</span>
              {packs.length === 0 && <p className="text-[13px] text-muted-foreground">Chưa đọc được danh sách gói (core chưa chạy?).</p>}
              {packs.map((pk) => {
                const added = policy.rules.some((r) => r.source === `pack-${pk.id}`);
                return (
                  <div key={pk.id} className="flex items-start gap-2 rounded-md border border-border bg-card p-1.5">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-xs font-medium text-foreground">{pk.name}</div>
                      <div className="line-clamp-2 text-[12px] text-muted-foreground">{pk.description}</div>
                      <a
                        href={pk.sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[12px] text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" /> Trang chính thức
                      </a>
                    </div>
                    <button
                      type="button"
                      disabled={srcBusy !== null}
                      onClick={() => addPack(pk)}
                      className="h-8 shrink-0 rounded-md border border-border bg-card px-2 text-xs text-foreground hover:bg-accent disabled:opacity-50"
                    >
                      {srcBusy === pk.id ? "Đang thêm…" : added ? "Cập nhật" : `Thêm (${pk.ruleCount})`}
                    </button>
                  </div>
                );
              })}
            </div>

            <div className="space-y-1">
              <span className="text-[13px] text-muted-foreground">Tải tệp lên (.json, .txt, .md, .csv)</span>
              <input
                ref={fileRef}
                type="file"
                accept=".json,.txt,.md,.csv,text/plain,application/json"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) onFile(f);
                  e.target.value = "";
                }}
              />
              <div className="flex gap-1.5">
                <button
                  type="button"
                  disabled={srcBusy !== null}
                  onClick={() => fileRef.current?.click()}
                  className={cn(field, "flex h-8 flex-1 items-center justify-center gap-1.5 hover:bg-accent disabled:opacity-50")}
                >
                  <Upload className="h-3.5 w-3.5" /> {srcBusy === "file" ? "Đang nhập…" : "Chọn tệp để nhập"}
                </button>
                <button
                  type="button"
                  onClick={exportPolicy}
                  title="Tải chính sách hiện tại xuống (.json)"
                  className={cn(field, "flex h-8 items-center justify-center gap-1.5 px-2.5 hover:bg-accent")}
                >
                  <Download className="h-3.5 w-3.5" /> Xuất
                </button>
              </div>
              <p className="text-[12px] leading-relaxed text-muted-foreground">
                Văn bản: mỗi dòng một từ; <code>Nhóm: từ1, từ2</code> hoặc <code># Nhóm</code> để đặt nhóm. JSON: xuất từ chính sách khác.
              </p>
            </div>

            <div className="space-y-1">
              <span className="text-[13px] text-muted-foreground">Lấy từ trang chính sách của nền tảng (URL https)</span>
              <div className="flex gap-1.5">
                <input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://support.google.com/youtube/answer/…"
                  className={cn(field, "h-8 min-w-0 flex-1")}
                />
                <button
                  type="button"
                  disabled={!/^https:\/\//.test(url.trim()) || srcBusy !== null}
                  onClick={onUrl}
                  className={cn(field, "h-8 shrink-0 px-3 hover:bg-accent disabled:opacity-50")}
                >
                  {srcBusy === "url" ? "Đang lấy…" : "Lấy"}
                </button>
              </div>
              <p className="text-[12px] leading-relaxed text-muted-foreground">
                Trang được lưu làm tài liệu tham chiếu của dự án; từ cấm cần bạn chọn thêm (trang chính sách là văn xuôi, không tự suy ra danh sách từ). Một số nền tảng (vd. TikTok) chặn truy cập tự động.
              </p>
              {page && (
                <details className="rounded-md border border-border bg-card p-1.5 text-[12px]">
                  <summary className="cursor-pointer text-foreground">Xem nội dung đã lấy: {page.title}</summary>
                  <pre className="nowheel mt-1 max-h-48 overflow-y-auto whitespace-pre-wrap break-words text-muted-foreground">{page.text.slice(0, 6000)}</pre>
                </details>
              )}
            </div>

            {(policy.references || []).length > 0 && (
              <div className="space-y-1">
                <span className="text-[13px] text-muted-foreground">Tài liệu tham chiếu ({policy.references!.length})</span>
                {policy.references!.map((r) => (
                  <a
                    key={r.url}
                    href={r.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 rounded-md border border-border bg-card px-2 py-1 text-[12px] text-foreground hover:bg-accent"
                  >
                    <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground" />
                    <span className="min-w-0 flex-1 truncate">{r.title || r.url}</span>
                    {r.fetchedAt && <span className="shrink-0 text-muted-foreground">{r.fetchedAt}</span>}
                  </a>
                ))}
              </div>
            )}
            {srcMsg && <p className="rounded bg-muted p-1.5 text-[13px] text-foreground">{srcMsg}</p>}
          </div>
        </Reveal>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <label className="block space-y-1">
          <span className="text-[13px] text-muted-foreground">Mức xử lý</span>
          <select
            value={policy.mode}
            onChange={(e) => patch({ mode: e.target.value as ContentPolicy["mode"] })}
            className={cn(field, "h-8 w-full")}
          >
            <option value="standard">Chuẩn: chỉ chặn mức "chặn"</option>
            <option value="strict">Nghiêm ngặt: cảnh báo cũng chặn</option>
          </select>
        </label>
        <div className="space-y-1">
          <span className="text-[13px] text-muted-foreground">Phạm vi kiểm</span>
          <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
            {Object.keys(SCOPE_LABEL).map((k) => (
              <label key={k} className="flex items-center gap-1 text-[13px] text-foreground">
                <input
                  type="checkbox"
                  checked={(policy.scopes as any)[k] !== false}
                  onChange={(e) => patch({ scopes: { ...policy.scopes, [k]: e.target.checked } })}
                />
                {SCOPE_LABEL[k]}
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Quy tắc ({policy.rules.length})</span>
          <button
            type="button"
            onClick={addRule}
            className="inline-flex items-center gap-1 rounded border border-border bg-card px-1.5 py-0.5 text-xs text-foreground hover:bg-accent"
          >
            <Plus className="h-3 w-3" /> Thêm
          </button>
        </div>
        {policy.rules.map((r) => (
          <div key={r.id} className="rounded-md border border-border">
            <div className="flex items-center gap-2 px-2 py-1.5">
              <input
                type="checkbox"
                checked={r.enabled}
                onChange={(e) => patchRule(r.id, { enabled: e.target.checked })}
                title="Bật/tắt quy tắc"
              />
              <button
                type="button"
                onClick={() => setOpen(open === r.id ? null : r.id)}
                className="min-w-0 flex-1 truncate text-left text-xs text-foreground"
              >
                {r.label}
                <span className="text-muted-foreground"> · {r.terms.length} từ</span>
                {r.source && <span className="ml-1 rounded bg-muted px-1 text-[11px] text-muted-foreground">{r.source.replace(/^pack-/, "gói ").replace(/^upload-/, "tệp ")}</span>}
              </button>
              <span
                className={cn(
                  "shrink-0 rounded px-1.5 py-0.5 text-[12px]",
                  r.severity === "block" ? "bg-destructive/10 text-destructive" : "bg-muted text-muted-foreground"
                )}
              >
                {r.severity === "block" ? "Chặn" : "Cảnh báo"}
              </span>
            </div>
            {open === r.id && (
              <div className="space-y-2 border-t border-border p-2">
                <div className="flex gap-1.5">
                  <input
                    value={r.label}
                    onChange={(e) => patchRule(r.id, { label: e.target.value })}
                    aria-label="Tên quy tắc"
                    className={cn(field, "h-8 min-w-0 flex-1")}
                  />
                  <select
                    value={r.severity}
                    onChange={(e) => patchRule(r.id, { severity: e.target.value as PolicyRule["severity"] })}
                    className={cn(field, "h-8 w-[100px] shrink-0")}
                  >
                    <option value="block">Chặn</option>
                    <option value="warn">Cảnh báo</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => patch({ rules: policy.rules.filter((x) => x.id !== r.id) })}
                    title="Xoá quy tắc"
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                <label className="block space-y-1">
                  <span className="text-[13px] text-muted-foreground">Từ / cụm từ (mỗi dòng một mục, giữ dấu tiếng Việt)</span>
                  <textarea
                    rows={4}
                    value={r.terms.join("\n")}
                    onChange={(e) => patchRule(r.id, { terms: e.target.value.split("\n") })}
                    className={cn(field, "w-full resize-y p-2 font-mono")}
                  />
                </label>
              </div>
            )}
          </div>
        ))}
      </div>

      <label className="block space-y-1">
        <span className="text-[13px] text-muted-foreground">Danh sách ngoại lệ (cụm từ được phép, mỗi dòng một mục)</span>
        <textarea
          rows={2}
          value={policy.allowlist.join("\n")}
          onChange={(e) => patch({ allowlist: e.target.value.split("\n") })}
          className={cn(field, "w-full resize-y p-2")}
        />
      </label>

      {msg && <p className="rounded bg-muted p-1.5 text-[13px] text-foreground">{msg}</p>}
      <button
        type="button"
        disabled={!dirty || busy}
        onClick={save}
        className={cn(
          "h-8 rounded-md px-3 text-xs font-medium",
          dirty ? "bg-foreground text-background hover:opacity-90" : "bg-muted text-muted-foreground"
        )}
      >
        {busy ? "Đang lưu…" : "Lưu chính sách"}
      </button>

      <div className="space-y-1.5 border-t border-border pt-3">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" /> Thử nhanh một đoạn văn bản (theo chính sách đã lưu)
        </span>
        <textarea
          rows={3}
          value={sample}
          onChange={(e) => setSample(e.target.value)}
          placeholder="Dán lời thoại / caption / kịch bản…"
          className={cn(field, "w-full resize-y p-2")}
        />
        <button
          type="button"
          onClick={test}
          disabled={!sample.trim()}
          className="h-8 rounded-md border border-border bg-card px-3 text-xs text-foreground hover:bg-accent disabled:opacity-50"
        >
          Kiểm tra
        </button>
        {report && (
          <div className="space-y-1">
            <p className={cn("text-[13px] font-medium", report.passed ? "text-semantic-success" : "text-destructive")}>
              {report.violations.length === 0
                ? "Đạt — không có từ ngữ vi phạm."
                : `${report.blockCount} chặn · ${report.warnCount} cảnh báo`}
            </p>
            {report.violations.map((v, i) => (
              <p key={i} className="rounded bg-muted/50 p-1.5 text-[13px] text-foreground">
                <b>{v.term}</b> <span className="text-muted-foreground">· {v.category}</span>
                <br />
                <span className="text-muted-foreground">…{v.snippet}…</span>
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
