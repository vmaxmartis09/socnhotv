import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

// 1. TemplatesView.tsx
const tplFile = path.join(dashboardDir, "components/templates/TemplatesView.tsx");
let tpl = fs.readFileSync(tplFile, "utf8").replace(/\r\n/g, "\n");

const oldFetchTpl = `  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/templates");
      const data = await res.json();
      if (data.ok && Array.isArray(data.templates)) {
        setTemplates(data.templates);
      } else {
        setError(data.error || "Không thể tải danh sách template");
      }
    } catch (err: any) {
      setError(err.message || "Lỗi mạng khi tải template");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);`;

const newFetchTpl = `  const fetchTemplates = async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/templates", { signal });
      const data = await res.json();
      if (signal?.aborted) return;
      if (data.ok && Array.isArray(data.templates)) {
        setTemplates(data.templates);
      } else {
        setError(data.error || "Không thể tải danh sách template");
      }
    } catch (err: any) {
      if (err.name === "AbortError" || signal?.aborted) return;
      setError(err.message || "Lỗi mạng khi tải template");
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchTemplates(controller.signal);
    return () => controller.abort();
  }, []);`;

tpl = tpl.replace(oldFetchTpl, newFetchTpl);
fs.writeFileSync(tplFile, tpl, "utf8");
console.log("Updated TemplatesView.tsx with AbortController");

// 2. ProjectHub.tsx
const hubFile = path.join(dashboardDir, "components/project/ProjectHub.tsx");
let hub = fs.readFileSync(hubFile, "utf8").replace(/\r\n/g, "\n");

const oldCharCount = `  React.useEffect(() => {
    setCharCount(null);
    getRepository().listCharacters(activeProjectId).then((l) => setCharCount(l.length)).catch(() => setCharCount(0));
  }, [activeProjectId]);`;

const newCharCount = `  React.useEffect(() => {
    let alive = true;
    setCharCount(null);
    getRepository()
      .listCharacters(activeProjectId)
      .then((l) => alive && setCharCount(l.length))
      .catch(() => alive && setCharCount(0));
    return () => {
      alive = false;
    };
  }, [activeProjectId]);`;

hub = hub.replace(oldCharCount, newCharCount);

const oldLibFetch = `  useEffect(() => {
    setError("");
    fetchProjectLibrary(activeProjectId).then(setLib).catch((e) => setError(String(e.message ?? e)));
  }, [activeProjectId]);`;

const newLibFetch = `  useEffect(() => {
    let alive = true;
    setError("");
    fetchProjectLibrary(activeProjectId)
      .then((res) => alive && setLib(res))
      .catch((e) => alive && setError(String(e.message ?? e)));
    return () => {
      alive = false;
    };
  }, [activeProjectId]);`;

hub = hub.replace(oldLibFetch, newLibFetch);
fs.writeFileSync(hubFile, hub, "utf8");
console.log("Updated ProjectHub.tsx with alive check and anti-race condition");

// 3. ProjectsTab.tsx
const ptabFile = path.join(dashboardDir, "components/project/ProjectsTab.tsx");
let ptab = fs.readFileSync(ptabFile, "utf8").replace(/\r\n/g, "\n");

const oldPtabEffect = `  React.useEffect(() => {
    setChars(null);
    setLib(null);
    getRepository().listCharacters(project.id).then(setChars).catch(() => setChars([]));
    fetchProjectLibrary(project.id).then(setLib).catch(() => setLib(null));
  }, [project.id]);`;

const newPtabEffect = `  React.useEffect(() => {
    let alive = true;
    setChars(null);
    setLib(null);
    getRepository().listCharacters(project.id).then((c) => alive && setChars(c)).catch(() => alive && setChars([]));
    fetchProjectLibrary(project.id).then((l) => alive && setLib(l)).catch(() => alive && setLib(null));
    return () => {
      alive = false;
    };
  }, [project.id]);`;

ptab = ptab.replace(oldPtabEffect, newPtabEffect);
fs.writeFileSync(ptabFile, ptab, "utf8");
console.log("Updated ProjectsTab.tsx with anti-race check");

// 4. VoiceSelectorWithClone.tsx
const voiceFile = path.join(dashboardDir, "components/voice/VoiceSelectorWithClone.tsx");
let voice = fs.readFileSync(voiceFile, "utf8").replace(/\r\n/g, "\n");

const oldVoiceLoad = `  const loadVoices = async () => {
    const list = await fetchVoiceVault();
    setVoices(list);
  };

  useEffect(() => {
    loadVoices();
  }, []);`;

const newVoiceLoad = `  useEffect(() => {
    let alive = true;
    fetchVoiceVault()
      .then((list) => alive && setVoices(list))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);`;

voice = voice.replace(oldVoiceLoad, newVoiceLoad);
fs.writeFileSync(voiceFile, voice, "utf8");
console.log("Updated VoiceSelectorWithClone.tsx with alive check");

// 5. ToolboxPanel.tsx
const toolboxFile = path.join(dashboardDir, "components/toolbox/ToolboxPanel.tsx");
let tb = fs.readFileSync(toolboxFile, "utf8").replace(/\r\n/g, "\n");

const oldTbRefresh = `  const refresh = useCallback(async () => {
    try {
      const [a, b, c] = await Promise.all([
        fetch("/api/toolbox?action=list").then((r) => r.json()),
        fetch("/api/toolbox?action=vaults").then((r) => r.json()),
        fetch("/api/toolbox?action=targets").then((r) => r.json()),
      ]);
      if (a.ok) setTools(a.tools);
      if (b.ok) setVaults(b.vaults);
      if (c.ok) setTargets(c);
      setLoadError(a.ok ? null : a.error || "Không đọc được danh mục công cụ");
    } catch (e: any) {
      setLoadError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);`;

const newTbRefresh = `  const refresh = useCallback(async (signal?: AbortSignal) => {
    try {
      const [a, b, c] = await Promise.all([
        fetch("/api/toolbox?action=list", { signal }).then((r) => r.json()),
        fetch("/api/toolbox?action=vaults", { signal }).then((r) => r.json()),
        fetch("/api/toolbox?action=targets", { signal }).then((r) => r.json()),
      ]);
      if (signal?.aborted) return;
      if (a.ok) setTools(a.tools);
      if (b.ok) setVaults(b.vaults);
      if (c.ok) setTargets(c);
      setLoadError(a.ok ? null : a.error || "Không đọc được danh mục công cụ");
    } catch (e: any) {
      if (e.name === "AbortError" || signal?.aborted) return;
      setLoadError(e.message);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);`;

tb = tb.replace(oldTbRefresh, newTbRefresh);
fs.writeFileSync(toolboxFile, tb, "utf8");
console.log("Updated ToolboxPanel.tsx with AbortController");

console.log("P-05 AbortController application finished.");
